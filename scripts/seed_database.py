#!/usr/bin/env python3
"""
Seed the SealCheck database from the JSON data files and markdown articles.

Reads:
    data/seal_types.json
    data/categories.json
    data/regulations.json
    data/articles/*.md

Insertion order:
    1. seal_types
    2. product_categories  (parents first, then children)
    3. product_keywords    (for each category)
    4. articles            (parsed from markdown with YAML frontmatter)

Uses upsert (ON CONFLICT ... DO UPDATE) so the script is idempotent.

Usage:
    python scripts/seed_database.py
"""

import json
import os
import re
import sys
import uuid
from pathlib import Path

import yaml

# Ensure the project root is on sys.path so `app` is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import SessionLocal, engine, Base
from app.models import (  # noqa: F401 -- models must be imported for metadata
    ProductCategory,
    ProductKeyword,
    SealType,
    Report,
    Article,
)

DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(filename: str) -> list[dict]:
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_article(filepath: Path) -> dict:
    """
    Parse a markdown file with YAML frontmatter.

    Expected format:
        ---
        title: "..."
        slug: "..."
        meta_description: "..."
        published: true
        ---
        <markdown body>

    Returns a dict with keys: title, slug, meta_description, published, content.
    """
    text = filepath.read_text(encoding="utf-8")

    # Split on the YAML frontmatter delimiters.
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not parse frontmatter in {filepath}")

    frontmatter_str = match.group(1)
    body = match.group(2).strip()

    frontmatter = yaml.safe_load(frontmatter_str)

    return {
        "title": frontmatter.get("title", filepath.stem),
        "slug": frontmatter.get("slug", filepath.stem),
        "meta_description": frontmatter.get("meta_description"),
        "published": frontmatter.get("published", False),
        "content": body,
    }


def build_regulation_lookup(regulations: list[dict]) -> dict[str, dict]:
    """
    Build a dict keyed by regulation code for quick lookup.
    For compound codes like "21 CFR 211.132 / 21 CFR 700.25" or
    "DSHEA / FSMA", the key is the exact string from the category.

    We also index each individual code so partial matches work.
    """
    lookup: dict[str, dict] = {}
    for reg in regulations:
        code = reg["code"]
        lookup[code] = reg
    return lookup


def resolve_regulation(code: str | None, lookup: dict[str, dict]) -> tuple[str | None, str | None]:
    """
    Given a regulation_code from a category, resolve it to
    (regulation_name, regulation_summary).

    Handles compound codes by trying the full string first, then the first
    individual code.
    """
    if not code:
        return None, None

    # Exact match
    if code in lookup:
        reg = lookup[code]
        return reg.get("title"), reg.get("summary")

    # Try first component of a compound code (e.g., "21 CFR 211.132 / 21 CFR 700.25")
    parts = [p.strip() for p in code.split("/")]
    for part in parts:
        if part in lookup:
            reg = lookup[part]
            return reg.get("title"), reg.get("summary")

    return None, None


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def upsert_seal_types(session, seal_types_data: list[dict]) -> int:
    """Insert or update seal types. Returns count."""
    count = 0
    for st in seal_types_data:
        stmt = pg_insert(SealType.__table__).values(
            id=uuid.uuid4(),
            name=st["name"],
            slug=st["slug"],
            description=st.get("description"),
            how_to_check=st.get("how_to_check"),
            signs_of_tampering=st.get("signs_of_tampering"),
            common_products=st.get("common_products"),
            image_url=st.get("image_url"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "how_to_check": stmt.excluded.how_to_check,
                "signs_of_tampering": stmt.excluded.signs_of_tampering,
                "common_products": stmt.excluded.common_products,
                "image_url": stmt.excluded.image_url,
            },
        )
        session.execute(stmt)
        count += 1
    return count


def upsert_categories(
    session,
    categories_data: list[dict],
    regulation_lookup: dict[str, dict],
) -> tuple[int, int]:
    """
    Insert or update product categories and their keywords.

    Parents (parent_category is null) are inserted first, then children.
    Returns (category_count, keyword_count).
    """
    # Separate parents and children.
    parents = [c for c in categories_data if c.get("parent_category") is None]
    children = [c for c in categories_data if c.get("parent_category") is not None]

    slug_to_id: dict[str, uuid.UUID] = {}
    cat_count = 0
    kw_count = 0

    # -- Insert parents first ------------------------------------------------
    for cat in parents:
        reg_name, reg_summary = resolve_regulation(
            cat.get("regulation_code"), regulation_lookup
        )
        cat_id = uuid.uuid4()
        stmt = pg_insert(ProductCategory.__table__).values(
            id=cat_id,
            name=cat["name"],
            slug=cat["slug"],
            description=cat.get("description"),
            requires_seal=cat.get("requires_seal", True),
            regulation_code=cat.get("regulation_code"),
            regulation_name=reg_name,
            regulation_summary=reg_summary,
            seal_types=cat.get("seal_types"),
            seal_description=cat.get("seal_description"),
            what_to_do=cat.get("what_to_do"),
            parent_category_id=None,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "requires_seal": stmt.excluded.requires_seal,
                "regulation_code": stmt.excluded.regulation_code,
                "regulation_name": stmt.excluded.regulation_name,
                "regulation_summary": stmt.excluded.regulation_summary,
                "seal_types": stmt.excluded.seal_types,
                "seal_description": stmt.excluded.seal_description,
                "what_to_do": stmt.excluded.what_to_do,
                "parent_category_id": stmt.excluded.parent_category_id,
            },
        )
        result = session.execute(stmt)
        session.flush()

        # Retrieve the actual id (may differ if row already existed).
        row = session.execute(
            ProductCategory.__table__.select().where(
                ProductCategory.__table__.c.slug == cat["slug"]
            )
        ).first()
        if row:
            slug_to_id[cat["slug"]] = row.id

        cat_count += 1

        # Upsert keywords for this category.
        kw_count += _upsert_keywords(session, slug_to_id[cat["slug"]], cat.get("keywords", []))

    # -- Insert children -----------------------------------------------------
    for cat in children:
        parent_slug = cat["parent_category"]
        # If parent was not in this batch, look it up from the DB.
        if parent_slug not in slug_to_id:
            row = session.execute(
                ProductCategory.__table__.select().where(
                    ProductCategory.__table__.c.slug == parent_slug
                )
            ).first()
            if row:
                slug_to_id[parent_slug] = row.id
            else:
                print(f"  WARNING: parent category '{parent_slug}' not found for '{cat['slug']}'. Skipping.")
                continue

        parent_id = slug_to_id[parent_slug]
        reg_name, reg_summary = resolve_regulation(
            cat.get("regulation_code"), regulation_lookup
        )

        cat_id = uuid.uuid4()
        stmt = pg_insert(ProductCategory.__table__).values(
            id=cat_id,
            name=cat["name"],
            slug=cat["slug"],
            description=cat.get("description"),
            requires_seal=cat.get("requires_seal", True),
            regulation_code=cat.get("regulation_code"),
            regulation_name=reg_name,
            regulation_summary=reg_summary,
            seal_types=cat.get("seal_types"),
            seal_description=cat.get("seal_description"),
            what_to_do=cat.get("what_to_do"),
            parent_category_id=parent_id,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "requires_seal": stmt.excluded.requires_seal,
                "regulation_code": stmt.excluded.regulation_code,
                "regulation_name": stmt.excluded.regulation_name,
                "regulation_summary": stmt.excluded.regulation_summary,
                "seal_types": stmt.excluded.seal_types,
                "seal_description": stmt.excluded.seal_description,
                "what_to_do": stmt.excluded.what_to_do,
                "parent_category_id": stmt.excluded.parent_category_id,
            },
        )
        session.execute(stmt)
        session.flush()

        # Retrieve the actual id.
        row = session.execute(
            ProductCategory.__table__.select().where(
                ProductCategory.__table__.c.slug == cat["slug"]
            )
        ).first()
        if row:
            slug_to_id[cat["slug"]] = row.id

        cat_count += 1

        # Upsert keywords for this category.
        kw_count += _upsert_keywords(session, slug_to_id[cat["slug"]], cat.get("keywords", []))

    return cat_count, kw_count


def _upsert_keywords(session, category_id: uuid.UUID, keywords: list[str]) -> int:
    """Upsert keywords for a given category. Returns count."""
    count = 0
    for kw in keywords:
        stmt = pg_insert(ProductKeyword.__table__).values(
            id=uuid.uuid4(),
            category_id=category_id,
            keyword=kw,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_category_keyword",
            set_={"keyword": stmt.excluded.keyword},
        )
        session.execute(stmt)
        count += 1
    return count


def upsert_articles(session, articles_dir: Path) -> int:
    """Parse and upsert all markdown articles. Returns count."""
    count = 0
    md_files = sorted(articles_dir.glob("*.md"))
    for md_path in md_files:
        try:
            article = parse_article(md_path)
        except ValueError as exc:
            print(f"  WARNING: {exc}")
            continue

        stmt = pg_insert(Article.__table__).values(
            id=uuid.uuid4(),
            title=article["title"],
            slug=article["slug"],
            content=article["content"],
            meta_description=article.get("meta_description"),
            published=article.get("published", False),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "title": stmt.excluded.title,
                "content": stmt.excluded.content,
                "meta_description": stmt.excluded.meta_description,
                "published": stmt.excluded.published,
            },
        )
        session.execute(stmt)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("SealCheck Database Seeder")
    print("=" * 50)

    # Load source data
    print("\nLoading data files...")
    seal_types_data = load_json("seal_types.json")
    categories_data = load_json("categories.json")
    regulations_data = load_json("regulations.json")
    regulation_lookup = build_regulation_lookup(regulations_data)
    articles_dir = DATA_DIR / "articles"

    print(f"  seal_types.json     : {len(seal_types_data)} entries")
    print(f"  categories.json     : {len(categories_data)} entries")
    print(f"  regulations.json    : {len(regulations_data)} entries")
    print(f"  articles/*.md       : {len(list(articles_dir.glob('*.md')))} files")

    # Seed
    session = SessionLocal()
    try:
        print("\n1. Upserting seal types...")
        seal_count = upsert_seal_types(session, seal_types_data)
        print(f"   -> {seal_count} seal types")

        print("2. Upserting product categories & keywords...")
        cat_count, kw_count = upsert_categories(
            session, categories_data, regulation_lookup
        )
        print(f"   -> {cat_count} categories, {kw_count} keywords")

        print("3. Upserting articles...")
        article_count = upsert_articles(session, articles_dir)
        print(f"   -> {article_count} articles")

        session.commit()
        print("\nCommitted successfully.")
    except Exception:
        session.rollback()
        print("\nERROR: rolling back transaction.")
        raise
    finally:
        session.close()

    # Summary
    print("\n" + "=" * 50)
    print("Seed Summary")
    print("=" * 50)
    print(f"  Seal types  : {seal_count} inserted/updated")
    print(f"  Categories  : {cat_count} inserted/updated")
    print(f"  Keywords    : {kw_count} inserted/updated")
    print(f"  Articles    : {article_count} inserted/updated")
    print("=" * 50)
    print("Done.")


if __name__ == "__main__":
    main()
