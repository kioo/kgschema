"""
Health check endpoint.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_db

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    db: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns application status, database connection status, and version.
    """
    # Check database connection
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    
    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        db=db_status,
        version=settings.APP_VERSION,
    )
