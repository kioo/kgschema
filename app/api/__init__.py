"""API router aggregation."""
from fastapi import APIRouter

from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.entities import router as entities_router
from app.api.health import router as health_router
from app.api.import_export import router as import_export_router
from app.api.prompts import router as prompts_router
from app.api.relations import router as relations_router
from app.api.users import router as users_router
from app.api.versions import router as versions_router

router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(entities_router, prefix="/entities", tags=["Entities"])
router.include_router(relations_router, prefix="/relations", tags=["Relations"])
router.include_router(prompts_router)  # prefix in router definition
router.include_router(audit_router, prefix="/audit", tags=["Audit"])
router.include_router(versions_router, prefix="/versions", tags=["Versions"])
router.include_router(import_export_router, prefix="/import", tags=["Import/Export"])


