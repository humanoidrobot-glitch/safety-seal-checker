from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ReportCreate(BaseModel):
    """Schema for submitting a new problem report."""

    product_name: str = Field(..., min_length=1)
    brand: str | None = None
    upc: str | None = None
    store_name: str | None = None
    store_location: str | None = None
    description: str = Field(..., min_length=1)
    photo_url: str | None = None
    email: EmailStr | None = None


class ReportResponse(BaseModel):
    """Schema returned after a report is created."""

    id: UUID
    product_name: str
    brand: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
