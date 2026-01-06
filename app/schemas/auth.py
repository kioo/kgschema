"""
Authentication Pydantic schemas.
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request body."""
    refresh_token: str
