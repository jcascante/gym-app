"""
Security utilities for authentication and authorization.

This module provides functions for password hashing, JWT token creation/validation,
and OAuth2 authentication scheme configuration.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# OAuth2 scheme for token extraction from requests
# This tells FastAPI to look for a Bearer token in the Authorization header
# Supports both OAuth2 password flow and direct Bearer token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="OAuth2PasswordBearer"
)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string safe for database storage

    Example:
        >>> hashed = get_password_hash("mysecretpassword")
        >>> print(hashed)
        '$2b$12$...'

    Note:
        Bcrypt has a 72 byte limit. Passwords longer than 72 bytes will be truncated.
        Uses 12 rounds (cost factor) which takes ~250ms to hash (intentionally slow).
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')

    # Bcrypt has a 72 byte limit - truncate if necessary
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash password
    # Cost factor of 12 = 2^12 iterations (good balance of security and performance)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("mysecretpassword")
        >>> verify_password("mysecretpassword", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False

    Note:
        Uses constant-time comparison to prevent timing attacks.
        Bcrypt handles this internally.
    """
    # Convert strings to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # Truncate password if longer than 72 bytes (same as hashing)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Verify password using bcrypt's constant-time comparison
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Return False for any error (invalid hash format, etc.)
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with optional expiration time.

    Args:
        data: Dictionary containing claims to encode in the token (typically user_id, email)
        expires_delta: Optional custom expiration time. If not provided, uses ACCESS_TOKEN_EXPIRE_MINUTES from settings

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If data is empty or contains invalid types

    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    if not data:
        raise ValueError("Token data cannot be empty")

    to_encode = data.copy()

    # Get current UTC time (timezone-aware)
    now = datetime.now(timezone.utc)

    # Set expiration time
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
    })

    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the decoded token payload

    Raises:
        HTTPException: If token is invalid, expired, or malformed (401 Unauthorized)

    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": 1})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        'user@example.com'
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Validate that the token contains required claims
        if payload.get("sub") is None:
            raise credentials_exception

        return payload

    except JWTError as e:
        # Token is invalid, expired, or malformed
        raise credentials_exception from e


def verify_token_expiration(payload: Dict[str, Any]) -> bool:
    """
    Check if a decoded token payload has expired.

    Args:
        payload: Decoded JWT token payload

    Returns:
        True if token is still valid, False if expired

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_access_token(token)
        >>> verify_token_expiration(payload)
        True
    """
    exp = payload.get("exp")
    if exp is None:
        return False

    # Get current UTC time and compare with token expiration
    now = datetime.now(timezone.utc)
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    return now < exp_datetime
