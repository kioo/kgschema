"""
Common Pydantic schemas.
"""
from pydantic import BaseModel


class Message(BaseModel):
    """Generic message response."""
    detail: str


class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int
    page: int
    size: int
    pages: int
