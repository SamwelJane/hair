import re
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category
from app.models.enums import HairCategory

_LENGTH_RE = re.compile(r"\d+")

# Suppliers don't see the legacy Category picker (superseded by hair_category
# as the real classification) - derive/auto-create the matching Category row
# instead so Product.category_id (still required by the schema) stays
# populated without exposing that tree to them.
_CATEGORY_BY_HAIR_CATEGORY: dict[HairCategory, tuple[str, str]] = {
    HairCategory.BULK_HAIR: ("bundles", "Hair Bundles"),
    HairCategory.EXTENSION: ("extensions", "Extensions"),
    HairCategory.WIG: ("wigs", "Wigs"),
    HairCategory.CLOSURE: ("closures", "Closures"),
    HairCategory.FRONTAL: ("frontals", "Frontals"),
    HairCategory.MACHINE_WEFT: ("machine-wefts", "Machine Wefts"),
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_wig_features(raw: str | None) -> list[str]:
    """Splits a comma-separated "Elastic band, Combs, Adjustable straps"
    input into a clean string list."""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def parse_length_inches(raw: str | None) -> int | None:
    """Extracts the leading number from a length string like "24 inches" ->
    24, or None if none found."""
    if not raw:
        return None
    match = _LENGTH_RE.search(raw)
    return int(match.group()) if match else None


async def resolve_category_id_for_hair_category(db: AsyncSession, hair_category: HairCategory) -> uuid.UUID:
    slug, name = _CATEGORY_BY_HAIR_CATEGORY[hair_category]
    existing = await db.scalar(select(Category).where(Category.slug == slug))
    if existing is not None:
        return existing.id

    stmt = insert(Category).values(name=name, slug=slug).on_conflict_do_nothing(index_elements=["slug"])
    await db.execute(stmt)
    await db.commit()
    category = await db.scalar(select(Category).where(Category.slug == slug))
    assert category is not None
    return category.id
