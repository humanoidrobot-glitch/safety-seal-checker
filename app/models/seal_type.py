"""
SealType model.
"""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SealType(Base):
    __tablename__ = "seal_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    how_to_check: Mapped[str | None] = mapped_column(Text, nullable=True)
    signs_of_tampering: Mapped[list | None] = mapped_column(JSON, nullable=True)
    common_products: Mapped[list | None] = mapped_column(JSON, nullable=True)
    image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
