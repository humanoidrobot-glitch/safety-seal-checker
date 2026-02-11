from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article
from app.schemas.article import ArticleDetail, ArticleSummary

router = APIRouter(tags=["articles"])


@router.get("/articles", response_model=list[ArticleSummary])
def list_articles(
    db: Session = Depends(get_db),
):
    """List all published articles."""
    articles = (
        db.query(Article)
        .filter(Article.published == True)  # noqa: E712
        .order_by(Article.created_at.desc())
        .all()
    )
    return [ArticleSummary.model_validate(a) for a in articles]


@router.get("/articles/{slug}", response_model=ArticleDetail)
def get_article(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a single article by slug (only if published)."""
    article = (
        db.query(Article)
        .filter(Article.slug == slug, Article.published == True)  # noqa: E712
        .first()
    )

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleDetail.model_validate(article)
