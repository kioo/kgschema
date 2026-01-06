"""
Entity and EntityProperty models.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.relation import Relation


class Entity(Base, UUIDMixin, TimestampMixin):
    """Entity definition."""
    
    __tablename__ = "entities"
    
    entity_code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(256), nullable=False)
    entity_name_en: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT", index=True)  # DRAFT / ACTIVE
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    properties: Mapped[list["EntityProperty"]] = relationship(
        "EntityProperty",
        back_populates="entity",
        cascade="all, delete-orphan",
        order_by="EntityProperty.display_order",
    )
    head_relations: Mapped[list["Relation"]] = relationship(
        "Relation",
        foreign_keys="Relation.head_entity_id",
        back_populates="head_entity",
    )
    tail_relations: Mapped[list["Relation"]] = relationship(
        "Relation",
        foreign_keys="Relation.tail_entity_id",
        back_populates="tail_entity",
    )


class EntityProperty(Base, UUIDMixin, TimestampMixin):
    """Entity property definition."""
    
    __tablename__ = "entity_properties"
    
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prop_code: Mapped[str] = mapped_column(String(128), nullable=False)
    prop_name: Mapped[str] = mapped_column(String(256), nullable=False)
    prop_name_en: Mapped[str | None] = mapped_column(String(256))
    data_type: Mapped[str] = mapped_column(String(32), nullable=False, default="STRING")  # STRING/INTEGER/FLOAT/BOOLEAN/ENUM
    options_json: Mapped[dict | None] = mapped_column(JSONB)  # For ENUM: ["A", "B", "C"]
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    entity: Mapped["Entity"] = relationship("Entity", back_populates="properties")
    
    __table_args__ = (
        # Unique constraint: prop_code unique within entity
        {"sqlite_autoincrement": True},
    )
