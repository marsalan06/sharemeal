from firebase_admin import messaging
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK for FCM only (not for auth)
# This uses Workload Identity Federation on Cloud Run
try:
    import firebase_admin
    from firebase_admin import credentials
    
    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        # On Cloud Run, use default credentials (WIF)
        if os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("K_SERVICE"):
            firebase_admin.initialize_app()
            logger.info("Firebase Admin initialized for FCM with Workload Identity Federation")
        else:
            # Local development - use service account file
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized for FCM with service account file")
            else:
                logger.warning("Firebase credentials not found. FCM notifications will fail.")
except Exception as e:
    logger.error(f"Error initializing Firebase Admin for FCM: {e}")
    # Don't raise - allow app to continue without FCM


async def send_notification(fcm_token: str, title: str, body: str):
    """Send FCM notification to a device"""
    try:
        logger.info(f"Sending FCM notification: {title} to token: {fcm_token[:20]}...")
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=fcm_token
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent FCM message: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
        raise
