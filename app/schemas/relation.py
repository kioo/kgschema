"""
Relation and RelationProperty Pydantic schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================
# Relation Property Schemas
# ============================================

class RelationPropertyBase(BaseModel):
    """Base schema for relation property."""
    prop_code: str = Field(..., min_length=1, max_length=128)
    prop_name: str = Field(..., min_length=1, max_length=256)
    prop_name_en: str | None = Field(None, max_length=256)
    data_type: str = Field("STRING", pattern="^(STRING|INTEGER|FLOAT|BOOLEAN|ENUM)$")
    options_json: list[str] | None = None
    is_required: bool = False
    display_order: int = 0


class RelationPropertyCreate(RelationPropertyBase):
    """Schema for creating a relation property."""
    pass


class RelationPropertyUpdate(BaseModel):
    """Schema for updating a relation property."""
    prop_name: str | None = Field(None, max_length=256)
    prop_name_en: str | None = Field(None, max_length=256)
    data_type: str | None = Field(None, pattern="^(STRING|INTEGER|FLOAT|BOOLEAN|ENUM)$")
    options_json: list[str] | None = None
    is_required: bool | None = None
    display_order: int | None = None


class RelationPropertyResponse(RelationPropertyBase):
    """Schema for relation property response."""
    id: uuid.UUID
    relation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Relation Schemas
# ============================================

class RelationBase(BaseModel):
    """Base schema for relation."""
    relation_code: str = Field(..., min_length=1, max_length=128, pattern="^[a-zA-Z0-9_]+$")
    relation_name: str = Field(..., min_length=1, max_length=256)
    relation_name_en: str | None = Field(None, max_length=256)
    head_entity_id: uuid.UUID
    tail_entity_id: uuid.UUID
    description: str | None = None


class RelationCreate(RelationBase):
    """Schema for creating a relation."""
    pass


class RelationUpdate(BaseModel):
    """Schema for updating a relation."""
    relation_name: str | None = Field(None, max_length=256)
    relation_name_en: str | None = Field(None, max_length=256)
    head_entity_id: uuid.UUID | None = None
    tail_entity_id: uuid.UUID | None = None
    description: str | None = None
    status: str | None = Field(None, pattern="^(DRAFT|ACTIVE)$")


class RelationResponse(RelationBase):
    """Schema for relation response."""
    id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Include entity names for convenience
    head_entity_code: str | None = None
    tail_entity_code: str | None = None

    model_config = {"from_attributes": True}


class RelationDetailResponse(RelationResponse):
    """Schema for relation detail response with properties."""
    properties: list[RelationPropertyResponse] = []


class RelationListResponse(BaseModel):
    """Schema for paginated relation list."""
    items: list[RelationResponse]
    total: int
    page: int
    size: int
    pages: int
