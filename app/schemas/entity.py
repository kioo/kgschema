"""
Entity and EntityProperty Pydantic schemas.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================
# Entity Property Schemas
# ============================================

class EntityPropertyBase(BaseModel):
    """Base schema for entity property."""
    prop_code: str = Field(..., min_length=1, max_length=128)
    prop_name: str = Field(..., min_length=1, max_length=256)
    prop_name_en: str | None = Field(None, max_length=256)
    data_type: str = Field("STRING", pattern="^(STRING|INTEGER|FLOAT|BOOLEAN|ENUM)$")
    options_json: list[str] | None = None
    is_required: bool = False
    display_order: int = 0


class EntityPropertyCreate(EntityPropertyBase):
    """Schema for creating an entity property."""
    pass


class EntityPropertyUpdate(BaseModel):
    """Schema for updating an entity property."""
    prop_name: str | None = Field(None, max_length=256)
    prop_name_en: str | None = Field(None, max_length=256)
    data_type: str | None = Field(None, pattern="^(STRING|INTEGER|FLOAT|BOOLEAN|ENUM)$")
    options_json: list[str] | None = None
    is_required: bool | None = None
    display_order: int | None = None


class EntityPropertyResponse(EntityPropertyBase):
    """Schema for entity property response."""
    id: uuid.UUID
    entity_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Entity Schemas
# ============================================

class EntityBase(BaseModel):
    """Base schema for entity."""
    entity_code: str = Field(..., min_length=1, max_length=128, pattern="^[a-zA-Z0-9_]+$")
    entity_name: str = Field(..., min_length=1, max_length=256)
    entity_name_en: str | None = Field(None, max_length=256)
    description: str | None = None


class EntityCreate(EntityBase):
    """Schema for creating an entity."""
    pass


class EntityUpdate(BaseModel):
    """Schema for updating an entity."""
    entity_name: str | None = Field(None, max_length=256)
    entity_name_en: str | None = Field(None, max_length=256)
    description: str | None = None
    status: str | None = Field(None, pattern="^(DRAFT|ACTIVE)$")


class EntityResponse(EntityBase):
    """Schema for entity response."""
    id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityDetailResponse(EntityResponse):
    """Schema for entity detail response with properties."""
    properties: list[EntityPropertyResponse] = []


class EntityListResponse(BaseModel):
    """Schema for paginated entity list."""
    items: list[EntityResponse]
    total: int
    page: int
    size: int
    pages: int
