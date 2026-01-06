"""
Relation and RelationProperty models.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.entity import Entity


class Relation(Base, UUIDMixin, TimestampMixin):
    """Relation definition."""
    
    __tablename__ = "relations"
    
    relation_code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    relation_name: Mapped[str] = mapped_column(String(256), nullable=False)
    relation_name_en: Mapped[str | None] = mapped_column(String(256))
    head_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id"),
        nullable=False,
        index=True,
    )
    tail_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id"),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    head_entity: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[head_entity_id],
        back_populates="head_relations",
    )
    tail_entity: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[tail_entity_id],
        back_populates="tail_relations",
    )
    properties: Mapped[list["RelationProperty"]] = relationship(
        "RelationProperty",
        back_populates="relation",
        cascade="all, delete-orphan",
        order_by="RelationProperty.display_order",
    )


class RelationProperty(Base, UUIDMixin, TimestampMixin):
    """Relation property definition."""
    
    __tablename__ = "relation_properties"
    
    relation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("relations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prop_code: Mapped[str] = mapped_column(String(128), nullable=False)
    prop_name: Mapped[str] = mapped_column(String(256), nullable=False)
    prop_name_en: Mapped[str | None] = mapped_column(String(256))
    data_type: Mapped[str] = mapped_column(String(32), nullable=False, default="STRING")
    options_json: Mapped[dict | None] = mapped_column(JSONB)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    relation: Mapped["Relation"] = relationship("Relation", back_populates="properties")
