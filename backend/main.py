from fastapi import FastAPI, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import math
import os
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from auth import get_current_user, verify_password, get_password_hash, create_access_token
from database import get_db
from fcm import send_notification
from models import (
    FoodItemCreate,
    FoodItemUpdate,
    FoodItemResponse,
    RequestCreate,
    RequestResponse,
    RequestUpdate,
    FCMTokenUpdate,
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    PasswordChangeRequest,
    DeleteAccountRequest
)
from app_config import setup_app, setup_events

app = FastAPI(
    title="ShareMeal API",
    description="FastAPI backend for ShareMeal app with JWT authentication and MongoDB",
    version="1.0.0"
)

setup_app(app)
setup_events(app)

logger.info("ShareMeal API initialized")


# Routes

@app.get(
    "/",
    tags=["General"],
    summary="API Root",
    description="Welcome endpoint that returns basic API information"
)
def root():
    """Root endpoint - Returns API welcome message"""
    logger.info("Root endpoint accessed")
    return {"message": "ShareMeal API"}


@app.get(
    "/health",
    tags=["General"],
    summary="Health Check",
    description="Check API and database connection status. Returns service health information."
)
async def health_check():
    """Health check endpoint - Verifies API and MongoDB connection status"""
    try:
        # Check database connection
        db = await get_db()
        # Simple ping to verify connection
        await db.command("ping")
        logger.info("Health check passed")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=201,
    tags=["Authentication"],
    summary="Register New User",
    description="Create a new user account with email and password. Returns JWT access token for immediate authentication."
)
async def register(
    register_request: RegisterRequest,
    db=Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be securely hashed)
    - **name**: User's display name
    
    Returns an access token that can be used for authenticated requests.
    """
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": register_request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password (validation already done by Pydantic)
        hashed_password = get_password_hash(register_request.password)
        
        # Create user in MongoDB
        user_data = {
            "email": register_request.email,
            "name": register_request.name,
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.users.insert_one(user_data)
        user_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id, "email": register_request.email, "name": register_request.name}
        )
        
        # Get the created user (without password)
        user = await db.users.find_one({"_id": result.inserted_id})
        if user:
            user["id"] = str(user["_id"])
            user["uid"] = user["id"]  # For compatibility with existing code
            del user["_id"]
            del user["hashed_password"]  # Don't return password hash
        
        logger.info(f"User registered: {register_request.email}")
        
        return AuthResponse(
            access_token=access_token,
            user=user,
            message="Registration successful"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors (from Pydantic or bcrypt)
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post(
    "/auth/login",
    response_model=AuthResponse,
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate with email and password. Returns JWT access token for authenticated requests."
)
async def login(
    login_request: LoginRequest,
    db=Depends(get_db)
):
    """
    Login with email and password.
    
    - **email**: User's registered email address
    - **password**: User's password
    
    Returns an access token that expires in 7 days.
    """
    try:
        # Find user by email
        user = await db.users.find_one({"email": login_request.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(login_request.password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        user_id = str(user["_id"])
        access_token = create_access_token(
            data={"sub": user_id, "email": user.get("email"), "name": user.get("name")}
        )
        
        # Update last login time
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Prepare user response (without password)
        user_response = {
            "id": user_id,
            "uid": user_id,  # For compatibility with existing code
            "email": user.get("email"),
            "name": user.get("name"),
            "picture": user.get("picture"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at")
        }
        
        logger.info(f"User logged in: {login_request.email}")
        
        return AuthResponse(
            access_token=access_token,
            user=user_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get(
    "/food",
    response_model=List[FoodItemResponse],
    tags=["Food Items"],
    summary="List Available Food Items",
    description="Get a list of all available food items with optional search and filter options. Only returns items that are still available (not expired)."
)
async def get_food_items(
    title: Optional[str] = Query(None, description="Search food items by title (case-insensitive)"),
    location: Optional[str] = Query(None, description="Search by pickup address or location name"),
    lat: Optional[float] = Query(None, description="Latitude for location-based search (requires lng and radius_km)"),
    lng: Optional[float] = Query(None, description="Longitude for location-based search (requires lat and radius_km)"),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers (requires lat and lng)"),
    item: Optional[str] = Query(None, description="Search by specific food item name (e.g., 'pizza', 'bread')"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get all available food items with optional search filters.
    
    **Search Options:**
    - Filter by title, location, or food item name
    - Location-based search using latitude, longitude, and radius
    - All searches are case-insensitive
    
    **Note:** Only returns food items that haven't expired (available_until is in the future).
    """
    # Base query: only available items
    query = {
        "available_until": {"$gte": datetime.now(timezone.utc).isoformat()}
    }
    
    # Add title filter
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    
    # Add location/address filter
    if location:
        query["pickup_address"] = {"$regex": location, "$options": "i"}
    
    # Add food item filter
    if item:
        query["items"] = {"$regex": item, "$options": "i"}
    
    # Get all matching items first
    food_items = await db.food_items.find(query).to_list(length=1000)
    
    # Filter by radius if lat/lng provided
    if lat is not None and lng is not None and radius_km is not None:
        filtered_items = []
        for food_item in food_items:
            item_lat = food_item.get("pickup_lat")
            item_lng = food_item.get("pickup_lng")
            if item_lat is not None and item_lng is not None:
                # Haversine distance calculation
                R = 6371  # Earth radius in km
                dlat = math.radians(item_lat - lat)
                dlng = math.radians(item_lng - lng)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(item_lat)) * math.sin(dlng/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance = R * c
                if distance <= radius_km:
                    filtered_items.append(food_item)
        food_items = filtered_items
    
    result = []
    for item in food_items:
        item["id"] = str(item["_id"])
        del item["_id"]
        result.append(FoodItemResponse(**item))
    return result


@app.post(
    "/food",
    response_model=FoodItemResponse,
    status_code=201,
    tags=["Food Items"],
    summary="Create Food Item",
    description="Post a new food item for sharing. Requires authentication. The current user becomes the donor."
)
async def create_food_item(
    food: FoodItemCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a new food item listing.
    
    **Required Fields:**
    - **title**: Name or title of the food listing
    - **pickup_lat**: Pickup location latitude
    - **pickup_lng**: Pickup location longitude
    - **pickup_address**: Human-readable pickup address
    - **quantity**: Amount of food available
    - **available_until**: ISO timestamp when food expires
    - **items**: List of food items (e.g., ["pizza", "bread", "salad"])
    
    The authenticated user automatically becomes the donor of this food item.
    """
    food_data = {
        "title": food.title,
        "pickup_lat": food.pickup_lat,
        "pickup_lng": food.pickup_lng,
        "pickup_address": food.pickup_address,
        "quantity": food.quantity,
        "available_until": food.available_until,
        "items": food.items,
        "donor_uid": current_user["uid"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.food_items.insert_one(food_data)
    response_data = food_data.copy()
    response_data["id"] = str(result.inserted_id)
    if "_id" in response_data:
        del response_data["_id"]
    
    return FoodItemResponse(**response_data)


@app.patch(
    "/food/{food_id}",
    response_model=FoodItemResponse,
    tags=["Food Items"],
    summary="Update Food Item",
    description="Update an existing food item. Only the owner (donor) can update their food listings."
)
async def update_food_item(
    food_id: str,
    food_update: FoodItemUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update a food item listing.
    
    - **food_id**: The ID of the food item to update
    - Only the owner (donor) who created the food item can update it
    - You can update any field by including it in the request body
    - Fields not included in the request remain unchanged
    """
    # Check if food item exists
    food = await db.food_items.find_one({"_id": ObjectId(food_id)})
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    # Check ownership
    if food["donor_uid"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only owner can update food item")
    
    # Build update dict (only include provided fields)
    update_data = {}
    if food_update.title is not None:
        update_data["title"] = food_update.title
    if food_update.pickup_lat is not None:
        update_data["pickup_lat"] = food_update.pickup_lat
    if food_update.pickup_lng is not None:
        update_data["pickup_lng"] = food_update.pickup_lng
    if food_update.pickup_address is not None:
        update_data["pickup_address"] = food_update.pickup_address
    if food_update.quantity is not None:
        update_data["quantity"] = food_update.quantity
    if food_update.available_until is not None:
        update_data["available_until"] = food_update.available_until
    if food_update.items is not None:
        update_data["items"] = food_update.items
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.food_items.update_one(
        {"_id": ObjectId(food_id)},
        {"$set": update_data}
    )
    
    updated_food = await db.food_items.find_one({"_id": ObjectId(food_id)})
    updated_food["id"] = str(updated_food["_id"])
    del updated_food["_id"]
    
    return FoodItemResponse(**updated_food)


@app.delete(
    "/food/{food_id}",
    tags=["Food Items"],
    summary="Delete Food Item",
    description="Delete a food item listing. Only the owner can delete their food items. All related requests are also deleted."
)
async def delete_food_item(
    food_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Delete a food item listing.
    
    - **food_id**: The ID of the food item to delete
    - Only the owner (donor) can delete their food items
    - This will also delete all pending/accepted requests for this food item
    """
    # Check if food item exists
    food = await db.food_items.find_one({"_id": ObjectId(food_id)})
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    # Check ownership
    if food["donor_uid"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only owner can delete food item")
    
    # Delete food item
    await db.food_items.delete_one({"_id": ObjectId(food_id)})
    
    # Optionally delete related requests
    await db.requests.delete_many({"food_id": food_id})
    
    return {"message": "Food item deleted successfully"}


@app.post(
    "/food/{food_id}/request",
    response_model=RequestResponse,
    status_code=201,
    tags=["Requests"],
    summary="Request Food Item",
    description="Create a request for a food item. The donor will receive a notification. You cannot request your own food items."
)
async def create_request(
    food_id: str,
    request_data: RequestCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a request for a food item.
    
    - **food_id**: The ID of the food item you want to request
    - **notes**: Optional message to the donor
    - You cannot request your own food items
    - The donor will receive a push notification (if they have FCM token set)
    - Request status starts as "pending"
    """
    # Get food item
    food = await db.food_items.find_one({"_id": ObjectId(food_id)})
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    if food["donor_uid"] == current_user["uid"]:
        raise HTTPException(status_code=400, detail="Cannot request your own food")
    
    # Create request
    request_doc = {
        "food_id": food_id,
        "requester_uid": current_user["uid"],
        "donor_uid": food["donor_uid"],
        "status": "pending",
        "notes": request_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.requests.insert_one(request_doc)
    response_data = request_doc.copy()
    response_data["id"] = str(result.inserted_id)
    if "_id" in response_data:
        del response_data["_id"]
    
    # Send notification to donor
    donor = await db.users.find_one({"_id": ObjectId(food["donor_uid"])})
    if donor and donor.get("fcm_token"):
        await send_notification(
            donor["fcm_token"],
            "New Food Request",
            f"{current_user.get('name', 'Someone')} requested your {food['title']}"
        )
    
    return RequestResponse(**response_data)


@app.get(
    "/requests",
    response_model=List[RequestResponse],
    tags=["Requests"],
    summary="Get My Requests",
    description="Get all food requests where you are either the donor (someone requested your food) or the requester (you requested someone's food)."
)
async def get_requests(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get all requests related to the current user.
    
    Returns requests where you are:
    - **Donor**: Someone requested your food items
    - **Requester**: You requested someone else's food items
    
    Includes all statuses: pending, accepted, and rejected.
    """
    requests = await db.requests.find({
        "$or": [
            {"donor_uid": current_user["uid"]},
            {"requester_uid": current_user["uid"]}
        ]
    }).to_list(length=100)
    
    result = []
    for req in requests:
        req["id"] = str(req["_id"])
        del req["_id"]
        result.append(RequestResponse(**req))
    return result


@app.patch(
    "/requests/{request_id}",
    response_model=RequestResponse,
    tags=["Requests"],
    summary="Update Request Status",
    description="Accept or reject a food request. Only the donor (food owner) can update request status. The requester will receive a notification."
)
async def update_request(
    request_id: str,
    update_data: RequestUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update the status of a food request.
    
    - **request_id**: The ID of the request to update
    - **status**: New status - must be "accepted", "rejected", or "pending"
    - Only the donor (food owner) can update request status
    - The requester will receive a push notification about the status change
    """
    request = await db.requests.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request["donor_uid"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only donor can update request")
    
    if update_data.status not in ["accepted", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    await db.requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": update_data.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated_request = await db.requests.find_one({"_id": ObjectId(request_id)})
    
    # Send notification to requester
    requester = await db.users.find_one({"_id": ObjectId(request["requester_uid"])})
    if requester and requester.get("fcm_token"):
        food = await db.food_items.find_one({"_id": ObjectId(request["food_id"])})
        food_title = food["title"] if food else "food item"
        
        status_msg = "accepted" if update_data.status == "accepted" else "rejected"
        await send_notification(
            requester["fcm_token"],
            f"Request {status_msg.capitalize()}",
            f"Your request for {food_title} has been {status_msg}"
        )
    
    updated_request["id"] = str(updated_request["_id"])
    del updated_request["_id"]
    return RequestResponse(**updated_request)


@app.delete(
    "/requests/{request_id}",
    tags=["Requests"],
    summary="Delete Request",
    description="Delete a food request. Both the requester and the donor can delete requests."
)
async def delete_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Delete a food request.
    
    - **request_id**: The ID of the request to delete
    - Both the requester and the donor can delete requests
    - Useful for canceling requests or removing unwanted requests
    """
    request = await db.requests.find_one({"_id": ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check if user is requester or donor
    if request["requester_uid"] != current_user["uid"] and request["donor_uid"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only requester or donor can delete request")
    
    await db.requests.delete_one({"_id": ObjectId(request_id)})
    
    return {"message": "Request deleted successfully"}


@app.get(
    "/user",
    tags=["User"],
    summary="Get My Profile",
    description="Get the current authenticated user's profile information."
)
async def get_user(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get current user profile.
    
    Returns your user information including:
    - User ID and email
    - Display name
    - Profile picture (if set)
    - FCM token status
    - Account creation and update timestamps
    """
    user = await db.users.find_one({"_id": ObjectId(current_user["uid"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare user response (without password)
    user_response = {
        "id": str(user["_id"]),
        "uid": str(user["_id"]),  # For compatibility with existing code
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "fcm_token": user.get("fcm_token"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at")
    }
    
    return user_response


@app.post(
    "/user/fcm-token",
    tags=["User"],
    summary="Update FCM Token",
    description="Update your Firebase Cloud Messaging (FCM) token to receive push notifications for food requests and status updates."
)
async def update_fcm_token(
    token_data: FCMTokenUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update your FCM token for push notifications.
    
    - **fcm_token**: Your Firebase Cloud Messaging token from the mobile app
    - This enables push notifications for:
      - New food requests on your listings
      - Request status updates (accepted/rejected)
    - Call this endpoint whenever your FCM token changes
    """
    await db.users.update_one(
        {"_id": ObjectId(current_user["uid"])},
        {
            "$set": {
                "fcm_token": token_data.fcm_token,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "FCM token updated"}


@app.post(
    "/user/change-password",
    tags=["User"],
    summary="Change Password",
    description="Change your account password. Requires your current password for verification."
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Change your account password.
    
    - **old_password**: Your current password (for verification)
    - **new_password**: Your new password (must meet password requirements)
    
    **Password Requirements:**
    - At least 8 characters long
    - Maximum 128 characters
    - Must contain at least one letter
    - Must contain at least one number
    
    **Security:**
    - Your current password must be verified before the change
    - The new password will be securely hashed before storage
    """
    try:
        # Get user from database
        user = await db.users.find_one({"_id": ObjectId(current_user["uid"])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify old password
        if not verify_password(password_data.old_password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Check if new password is different from old password
        if password_data.old_password == password_data.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from current password")
        
        # Hash new password
        hashed_password = get_password_hash(password_data.new_password)
        
        # Update password in database
        await db.users.update_one(
            {"_id": ObjectId(current_user["uid"])},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"Password changed for user: {current_user.get('email')}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Password change validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")


@app.delete(
    "/user",
    tags=["User"],
    summary="Delete Account",
    description="Permanently delete your user account. This action cannot be undone. All your food items and requests will be deleted."
)
async def delete_user(
    delete_request: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Permanently delete your user account.
    
    - **password**: Your current password (required for verification)
    
    **Warning:** This action is irreversible and will permanently delete:
    - Your user account
    - All food items you've posted
    - All requests you've made
    - All requests for your food items
    
    **Security:**
    - Your password must be verified before deletion
    - This action cannot be undone
    """
    try:
        # Get user from database
        user = await db.users.find_one({"_id": ObjectId(current_user["uid"])})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if not verify_password(delete_request.password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Password is incorrect")
        
        user_id = current_user["uid"]
        
        # Delete all food items created by the user
        food_items_deleted = await db.food_items.delete_many({"donor_uid": user_id})
        
        # Delete all requests where user is requester
        requests_as_requester_deleted = await db.requests.delete_many({"requester_uid": user_id})
        
        # Delete all requests where user is donor (for their food items)
        requests_as_donor_deleted = await db.requests.delete_many({"donor_uid": user_id})
        
        # Delete the user account
        await db.users.delete_one({"_id": ObjectId(user_id)})
        
        logger.info(
            f"User account deleted: {current_user.get('email')} "
            f"(Food items: {food_items_deleted.deleted_count}, "
            f"Requests as requester: {requests_as_requester_deleted.deleted_count}, "
            f"Requests as donor: {requests_as_donor_deleted.deleted_count})"
        )
        
        return {
            "message": "Account deleted successfully",
            "deleted_items": {
                "food_items": food_items_deleted.deleted_count,
                "requests_as_requester": requests_as_requester_deleted.deleted_count,
                "requests_as_donor": requests_as_donor_deleted.deleted_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Account deletion failed: {str(e)}")


if __name__ == "__main__":
    # Use PORT env var (Cloud Run sets this), default to 8000 for local dev
    port = int(os.getenv("PORT", 8000))
    # Enable reload in development (set RELOAD=false to disable)
    reload = os.getenv("RELOAD", "true").lower() == "true"
    logger.info(f"Starting server on port {port} (reload={reload})")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=reload)

