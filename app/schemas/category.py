from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CategorySummary(BaseModel):
    """Lightweight category representation used in lists and search results."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    requires_seal: bool
    regulation_code: str | None = None
    parent_category_id: UUID | None = None

    model_config = {"from_attributes": True}


class CategoryDetail(CategorySummary):
    """Full category detail including regulation info, seals, keywords, and relations."""

    regulation_name: str | None = None
    regulation_summary: str | None = None
    seal_types: list[str] = []
    seal_description: str | None = None
    what_to_do: str | None = None
    keywords: list[str] = []
    children: list[CategorySummary] = []
    parent: CategorySummary | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
