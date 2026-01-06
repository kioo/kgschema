"""API router aggregation."""
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.users import router as users_router

router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])

# Placeholder for future routers:
# router.include_router(entities_router, prefix="/entities", tags=["Entities"])
# router.include_router(relations_router, prefix="/relations", tags=["Relations"])
# router.include_router(versions_router, prefix="/versions", tags=["Versions"])
# router.include_router(audit_router, prefix="/audit", tags=["Audit"])
# router.include_router(import_export_router, tags=["Import/Export"])
