"""Prompt and PromptVersion models for prompt management with versioning."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
import uuid


class Prompt(Base, UUIDMixin, TimestampMixin):
    """Main prompt table - stores current/active version of each prompt."""
    __tablename__ = "prompts"
    
    # Core fields
    tag = Column(String(128), unique=True, nullable=False, index=True)  # Unique tag/identifier
    content = Column(Text, nullable=False)  # Current prompt content
    description = Column(Text, nullable=True)  # Description
    current_version = Column(Integer, nullable=False, default=1)  # Current version number
    is_active = Column(Boolean, nullable=False, default=True)  # Soft delete
    
    # Relationship to versions
    versions = relationship("PromptVersion", back_populates="prompt", lazy="dynamic",
                            order_by="PromptVersion.version.desc()")


class PromptVersion(Base, UUIDMixin, TimestampMixin):
    """Prompt version history - stores all historical versions."""
    __tablename__ = "prompt_versions"

    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)  # Version number
    content = Column(Text, nullable=False)  # Content at this version
    description = Column(Text, nullable=True)  # Description at this version
    change_note = Column(Text, nullable=True)  # Note about what changed

    # Relationship
    prompt = relationship("Prompt", back_populates="versions")

    __table_args__ = (
        # Unique constraint: one version number per prompt
        {"sqlite_autoincrement": True},
    )
