from pydantic import BaseModel

from app.schemas.category import CategorySummary


class SearchResult(BaseModel):
    """Wrapper for search results including query metadata."""

    categories: list[CategorySummary]
    query: str
    total: int
