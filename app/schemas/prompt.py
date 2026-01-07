"""Pydantic schemas for Prompt management."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ===== Prompt Schemas =====

class PromptBase(BaseModel):
    """Base prompt schema."""
    tag: str = Field(..., min_length=1, max_length=128, description="Unique tag/identifier")
    content: str = Field(..., min_length=1, description="Prompt content")
    description: Optional[str] = Field(None, description="Description")


class PromptCreate(PromptBase):
    """Schema for creating a prompt."""
    pass


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""
    content: Optional[str] = Field(None, min_length=1, description="Updated content")
    description: Optional[str] = Field(None, description="Updated description")
    create_version: bool = Field(True, description="Whether to save this as a new version")
    change_note: Optional[str] = Field(None, description="Note about changes (for version history)")


class PromptResponse(PromptBase):
    """Schema for prompt response."""
    id: str
    current_version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_uuid(cls, obj: Any) -> 'PromptResponse':
        """Create from ORM object with UUID to string conversion."""
        return cls.model_construct(
            id=str(obj.id),
            tag=obj.tag,
            content=obj.content,
            description=obj.description,
            current_version=obj.current_version,
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class PromptListResponse(BaseModel):
    """Schema for paginated prompt list."""
    items: List[PromptResponse]
    total: int
    page: int
    size: int
    pages: int


# ===== PromptVersion Schemas =====

class PromptVersionResponse(BaseModel):
    """Schema for prompt version response."""
    id: str
    prompt_id: str
    version: int
    content: str
    description: Optional[str]
    change_note: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm_with_uuid(cls, obj: Any) -> 'PromptVersionResponse':
        """Create from ORM object with UUID to string conversion."""
        return cls.model_construct(
            id=str(obj.id),
            prompt_id=str(obj.prompt_id),
            version=obj.version,
            content=obj.content,
            description=obj.description,
            change_note=obj.change_note,
            created_at=obj.created_at,
        )


class PromptVersionListResponse(BaseModel):
    """Schema for prompt version history."""
    items: List[PromptVersionResponse]
    total: int


class PromptDetailResponse(PromptResponse):
    """Detailed prompt response with version history."""
    versions: List[PromptVersionResponse] = []
