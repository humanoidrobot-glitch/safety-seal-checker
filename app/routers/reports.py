from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
):
    """Submit a new problem report."""
    report = Report(
        product_name=report_in.product_name,
        brand=report_in.brand,
        upc=report_in.upc,
        store_name=report_in.store_name,
        store_location=report_in.store_location,
        description=report_in.description,
        photo_url=report_in.photo_url,
        email=str(report_in.email) if report_in.email else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportResponse.model_validate(report)
