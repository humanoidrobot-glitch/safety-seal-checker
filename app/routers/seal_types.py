from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SealType
from app.schemas.seal_type import SealTypeResponse

router = APIRouter(tags=["seal-types"])


@router.get("/seal-types", response_model=list[SealTypeResponse])
def list_seal_types(
    db: Session = Depends(get_db),
):
    """List all seal types."""
    seal_types = db.query(SealType).order_by(SealType.name).all()
    return [SealTypeResponse.model_validate(st) for st in seal_types]
