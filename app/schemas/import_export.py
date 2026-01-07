"""
Import/Export Pydantic schemas.
"""
from typing import Any

from pydantic import BaseModel


class ImportError(BaseModel):
    """Schema for a single import error."""
    sheet: str
    row: int
    field: str
    value: str | None
    error: str


class ImportResult(BaseModel):
    """Schema for import result."""
    success: bool
    errors: list[ImportError] = []
    entities_count: int = 0
    relations_count: int = 0
    entity_properties_count: int = 0
    relation_properties_count: int = 0


class ExportData(BaseModel):
    """Schema for export data."""
    version: int | None = None
    exported_at: str
    entities: list[dict[str, Any]]
    relations: list[dict[str, Any]]
