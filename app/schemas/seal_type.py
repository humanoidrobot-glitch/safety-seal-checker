from uuid import UUID

from pydantic import BaseModel


class SealTypeResponse(BaseModel):
    """Seal type with full detail."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    how_to_check: str | None = None
    signs_of_tampering: list[str] = []
    common_products: list[str] = []
    image_url: str | None = None

    model_config = {"from_attributes": True}
