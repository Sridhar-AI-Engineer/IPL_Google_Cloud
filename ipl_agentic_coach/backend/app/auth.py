"""JWT token generation and verification for authentication."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # subject (user ID or username)
    exp: datetime  # expiration
    iat: datetime  # issued at
    aud: str  # audience
    iss: str  # issuer
    type: str  # token_type: access or refresh


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class User(BaseModel):
    """User info from token."""
    user_id: str
    username: Optional[str] = None
    is_admin: bool = False


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    is_admin: bool = False,
) -> str:
    """Generate JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expiration_hours
        )
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "aud": settings.token_audience,
        "iss": settings.token_issuer,
        "type": "access",
        "is_admin": is_admin,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """Generate JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expiration_days
    )
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "aud": settings.token_audience,
        "iss": settings.token_issuer,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.token_audience,
            issuer=settings.token_issuer,
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> User:
    """FastAPI dependency to extract user from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    
    payload = verify_token(token)
    
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    return User(
        user_id=payload.sub,
        username=payload.sub,
        is_admin=payload.__dict__.get("is_admin", False),
    )


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency to verify admin role."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
