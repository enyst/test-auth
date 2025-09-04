from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import os
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token encryption key (for GitHub tokens)
def get_encryption_key() -> bytes:
    """Get or generate encryption key for sensitive data"""
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        # Generate a key (in production, this should be stored securely)
        key = Fernet.generate_key().decode()
        os.environ["ENCRYPTION_KEY"] = key
    return key.encode() if isinstance(key, str) else key


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise ValueError("Invalid token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def encrypt_token(token: str) -> str:
    """Encrypt sensitive token for database storage"""
    if not token:
        return ""
    
    fernet = Fernet(get_encryption_key())
    encrypted_token = fernet.encrypt(token.encode())
    return base64.b64encode(encrypted_token).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt token from database"""
    if not encrypted_token:
        return ""
    
    try:
        fernet = Fernet(get_encryption_key())
        encrypted_bytes = base64.b64decode(encrypted_token.encode())
        decrypted_token = fernet.decrypt(encrypted_bytes)
        return decrypted_token.decode()
    except Exception:
        return ""


def create_github_oauth_token(github_user_data: Dict[str, Any], access_token: str) -> str:
    """Create JWT token with GitHub user data"""
    token_data = {
        "sub": github_user_data["login"],
        "github_id": github_user_data["id"],
        "email": github_user_data.get("email"),
        "avatar_url": github_user_data.get("avatar_url"),
        "github_token": access_token,  # Include GitHub access token
        "type": "github_oauth"
    }
    
    return create_access_token(token_data)