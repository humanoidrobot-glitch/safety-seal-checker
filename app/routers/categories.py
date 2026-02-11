from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.models import ProductCategory
from app.schemas.category import CategoryDetail, CategorySummary

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategorySummary])
def list_categories(
    parent_id: UUID | None = Query(None, description="Filter by parent category ID"),
    requires_seal: bool | None = Query(None, description="Filter by seal requirement"),
    db: Session = Depends(get_db),
):
    """List all categories with optional filters."""
    query = db.query(ProductCategory)

    if parent_id is not None:
        query = query.filter(ProductCategory.parent_category_id == parent_id)

    if requires_seal is not None:
        query = query.filter(ProductCategory.requires_seal == requires_seal)

    # Eagerly load parent info for each category
    query = query.options(joinedload(ProductCategory.parent_category))
    query = query.order_by(ProductCategory.name)

    categories = query.all()
    return [CategorySummary.model_validate(cat) for cat in categories]


@router.get("/categories/{slug}", response_model=CategoryDetail)
def get_category(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get full category detail by slug."""
    category = (
        db.query(ProductCategory)
        .options(
            selectinload(ProductCategory.keywords),
            selectinload(ProductCategory.subcategories),
            joinedload(ProductCategory.parent_category),
        )
        .filter(ProductCategory.slug == slug)
        .first()
    )

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Build the response, transforming keywords from model objects to strings
    return CategoryDetail(
        id=category.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        requires_seal=category.requires_seal,
        regulation_code=category.regulation_code,
        regulation_name=category.regulation_name,
        regulation_summary=category.regulation_summary,
        seal_types=category.seal_types or [],
        seal_description=category.seal_description,
        what_to_do=category.what_to_do,
        keywords=[kw.keyword for kw in category.keywords],
        children=[CategorySummary.model_validate(child) for child in category.subcategories],
        parent=CategorySummary.model_validate(category.parent_category) if category.parent_category else None,
        parent_category_id=category.parent_category_id,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )
