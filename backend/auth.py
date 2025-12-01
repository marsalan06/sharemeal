from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
import logging
import hashlib
import base64
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


def _prehash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 and encode as base64.
    This produces a consistent 44-byte string (well under bcrypt's 72-byte limit).
    """
    # SHA-256 produces 32 bytes, base64 encoding makes it 44 characters (bytes)
    hash_bytes = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.b64encode(hash_bytes).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Pre-hash the plain password to match the stored hash
    prehashed = _prehash_password(plain_password)
    return pwd_context.verify(prehashed, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using SHA-256 pre-hashing + bcrypt"""
    try:
        # Pre-hash with SHA-256 and base64 encode to ensure consistent 44-byte input for bcrypt
        # This avoids bcrypt's 72-byte limit while maintaining security
        prehashed = _prehash_password(password)
        logger.debug(f"Pre-hashed password length: {len(prehashed.encode('utf-8'))} bytes")
        return pwd_context.hash(prehashed)
    except ValueError as e:
        # Catch bcrypt's 72-byte limit error and provide better message
        error_msg = str(e)
        logger.error(f"Password hashing error: {error_msg}")
        if "72 bytes" in error_msg.lower() or "72" in error_msg:
            raise ValueError(
                "Password is too long. Maximum 72 bytes allowed. "
                "Some characters (like emojis or special Unicode) use multiple bytes. "
                "Please use a shorter password with standard characters."
            )
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password hashing: {str(e)}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str) -> dict:
    """Verify JWT token and return user info"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"uid": user_id, "email": payload.get("email"), "name": payload.get("name")}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token"""
    return await verify_token(credentials.credentials)
