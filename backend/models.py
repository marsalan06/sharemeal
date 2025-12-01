from pydantic import BaseModel, field_validator
from typing import Optional, List


class FoodItemCreate(BaseModel):
    title: str
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    quantity: str
    available_until: str
    items: List[str]


class FoodItemUpdate(BaseModel):
    title: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    pickup_address: Optional[str] = None
    quantity: Optional[str] = None
    available_until: Optional[str] = None
    items: Optional[List[str]] = None


class FoodItemResponse(BaseModel):
    id: str
    title: str
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    quantity: str
    available_until: str
    items: List[str]
    donor_uid: str
    created_at: str

    class Config:
        from_attributes = True


class RequestCreate(BaseModel):
    notes: Optional[str] = None


class RequestResponse(BaseModel):
    id: str
    food_id: str
    requester_uid: str
    donor_uid: str
    status: str
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class RequestUpdate(BaseModel):
    status: str  # "accepted", "rejected", "pending"


class FCMTokenUpdate(BaseModel):
    fcm_token: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        
        # Production-level password requirements
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if len(v) > 128:
            raise ValueError('Password cannot be longer than 128 characters')
        
        # Note: We don't check 72-byte limit here because passwords are pre-hashed
        # with SHA-256 before bcrypt, which handles any length password safely.
        
        # Optional: Check for at least one letter and one number (production best practice)
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_digit:
            raise ValueError('Password must contain at least one number')
        
        return v


class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Note: We don't check 72-byte limit here because passwords are pre-hashed
        # with SHA-256 before bcrypt, which handles any length password safely.
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    message: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
    
    @field_validator('old_password')
    @classmethod
    def validate_old_password(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Old password cannot be empty')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('New password cannot be empty')
        
        # Production-level password requirements
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        
        if len(v) > 128:
            raise ValueError('New password cannot be longer than 128 characters')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('New password must contain at least one letter')
        
        if not has_digit:
            raise ValueError('New password must contain at least one number')
        
        return v


class DeleteAccountRequest(BaseModel):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

