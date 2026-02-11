"""
ProductCategory and ProductKeyword models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_seal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    regulation_code: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    regulation_name: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    regulation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    seal_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    seal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_to_do: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    keywords: Mapped[list["ProductKeyword"]] = relationship(
        "ProductKeyword", back_populates="category", cascade="all, delete-orphan"
    )
    parent_category: Mapped["ProductCategory | None"] = relationship(
        "ProductCategory", remote_side="ProductCategory.id", backref="subcategories"
    )

    # Trigram index for full-text / fuzzy search on name
    __table_args__ = (
        Index(
            "ix_product_categories_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class ProductKeyword(Base):
    __tablename__ = "product_keywords"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    keyword: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # Relationships
    category: Mapped["ProductCategory"] = relationship(
        "ProductCategory", back_populates="keywords"
    )

    __table_args__ = (
        UniqueConstraint("category_id", "keyword", name="uq_category_keyword"),
        Index(
            "ix_product_keywords_keyword_trgm",
            "keyword",
            postgresql_using="gin",
            postgresql_ops={"keyword": "gin_trgm_ops"},
        ),
    )
