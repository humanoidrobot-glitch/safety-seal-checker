"""Initial schema: create all tables with indexes and trigram support.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable the pg_trgm extension for trigram/fuzzy search indexes.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # -- seal_types ----------------------------------------------------------
    op.create_table(
        "seal_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("how_to_check", sa.Text, nullable=True),
        sa.Column("signs_of_tampering", postgresql.JSON, nullable=True),
        sa.Column("common_products", postgresql.JSON, nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
    )

    # -- product_categories --------------------------------------------------
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "requires_seal",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("regulation_code", sa.String(100), nullable=True),
        sa.Column("regulation_name", sa.String(500), nullable=True),
        sa.Column("regulation_summary", sa.Text, nullable=True),
        sa.Column("seal_types", postgresql.JSON, nullable=True),
        sa.Column("seal_description", sa.Text, nullable=True),
        sa.Column("what_to_do", sa.Text, nullable=True),
        sa.Column(
            "parent_category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_categories.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # B-tree index on product_categories.slug (for exact lookups)
    op.create_index("ix_product_categories_slug", "product_categories", ["slug"])
    # GIN trigram index on product_categories.name (for fuzzy search)
    op.execute(
        "CREATE INDEX ix_product_categories_name_trgm "
        "ON product_categories USING gin (name gin_trgm_ops)"
    )

    # -- product_keywords ----------------------------------------------------
    op.create_table(
        "product_keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.UniqueConstraint("category_id", "keyword", name="uq_category_keyword"),
    )
    # B-tree index on product_keywords.keyword
    op.create_index("ix_product_keywords_keyword", "product_keywords", ["keyword"])
    # GIN trigram index on product_keywords.keyword (for fuzzy search)
    op.execute(
        "CREATE INDEX ix_product_keywords_keyword_trgm "
        "ON product_keywords USING gin (keyword gin_trgm_ops)"
    )

    # -- reports -------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("store_name", sa.String(255), nullable=True),
        sa.Column("store_location", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # -- articles ------------------------------------------------------------
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column(
            "published",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # B-tree index on articles.slug
    op.create_index("ix_articles_slug", "articles", ["slug"])


def downgrade() -> None:
    op.drop_table("articles")
    op.drop_table("reports")
    op.drop_table("product_keywords")
    op.drop_table("product_categories")
    op.drop_table("seal_types")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
