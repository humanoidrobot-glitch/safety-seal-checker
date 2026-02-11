from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ArticleSummary(BaseModel):
    """Lightweight article representation for listings."""

    id: UUID
    title: str
    slug: str
    meta_description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleSummary):
    """Full article including content body."""

    content: str
    updated_at: datetime

    model_config = {"from_attributes": True}
