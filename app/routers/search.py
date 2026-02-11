from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ProductCategory, ProductKeyword
from app.schemas.category import CategorySummary
from app.schemas.search import SearchResult

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResult)
def search_categories(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    db: Session = Depends(get_db),
):
    """
    Search categories by keyword match and category name match.

    Results are ranked by relevance:
      1. Exact keyword match
      2. Keyword starts with query
      3. Keyword contains query
      4. Category name contains query
    """
    query_lower = q.strip().lower()
    pattern = f"%{query_lower}%"

    # ----------------------------------------------------------------
    # 1. Find categories via keyword matches (ILIKE)
    # ----------------------------------------------------------------
    keyword_rows = (
        db.query(ProductKeyword)
        .options(joinedload(ProductKeyword.category))
        .filter(ProductKeyword.keyword.ilike(pattern))
        .all()
    )

    # Bucket each keyword hit by match quality
    EXACT = 0
    STARTS_WITH = 1
    CONTAINS = 2

    # category_id -> best (lowest) rank seen
    keyword_ranks: dict[str, int] = {}
    keyword_categories: dict[str, ProductCategory] = {}

    for kw_row in keyword_rows:
        kw_lower = kw_row.keyword.lower()
        cat = kw_row.category

        if kw_lower == query_lower:
            rank = EXACT
        elif kw_lower.startswith(query_lower):
            rank = STARTS_WITH
        else:
            rank = CONTAINS

        cat_id = str(cat.id)
        if cat_id not in keyword_ranks or rank < keyword_ranks[cat_id]:
            keyword_ranks[cat_id] = rank
            keyword_categories[cat_id] = cat

    # ----------------------------------------------------------------
    # 2. Find categories via name match (ILIKE)
    # ----------------------------------------------------------------
    NAME_MATCH = 3

    name_rows = (
        db.query(ProductCategory)
        .filter(ProductCategory.name.ilike(pattern))
        .all()
    )

    name_categories: dict[str, ProductCategory] = {}
    for cat in name_rows:
        cat_id = str(cat.id)
        name_categories[cat_id] = cat

    # ----------------------------------------------------------------
    # 3. Merge and deduplicate — keyword match wins over name match
    # ----------------------------------------------------------------
    all_ids = set(keyword_ranks.keys()) | set(name_categories.keys())
    ranked: list[tuple[int, str, ProductCategory]] = []

    for cat_id in all_ids:
        if cat_id in keyword_ranks:
            rank = keyword_ranks[cat_id]
            cat = keyword_categories[cat_id]
        else:
            rank = NAME_MATCH
            cat = name_categories[cat_id]
        ranked.append((rank, cat.name.lower(), cat))

    # Sort by rank first, then alphabetically by name for deterministic order
    ranked.sort(key=lambda t: (t[0], t[1]))

    categories = [
        CategorySummary.model_validate(cat) for _, _, cat in ranked
    ]

    return SearchResult(
        categories=categories,
        query=q,
        total=len(categories),
    )
