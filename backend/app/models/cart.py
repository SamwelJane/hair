import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class Cart(Base, UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin):
    """New vs. the old app, per an explicit scope decision: the old CartProvider
    was localStorage-only (device/browser-local, never synced). A cart here is
    identified either by user_id (signed in) or by an opaque guest_token
    (anonymous web/mobile client, stored client-side). On login, the guest
    cart's items are merged into the user's cart and the guest cart is
    deleted - see services/cart.py."""

    __tablename__ = "carts"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True
    )
    guest_token: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "cart_items"

    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="items")
