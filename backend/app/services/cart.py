import secrets
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.catalog import Product, ProductVariant


class ProductNotFoundError(Exception):
    pass


def generate_guest_token() -> str:
    return secrets.token_urlsafe(24)


async def get_or_create_cart(db: AsyncSession, *, user_id: uuid.UUID | None, guest_token: str | None) -> Cart:
    """A cart is identified either by user_id (signed in) or an opaque
    guest_token (anonymous web/mobile client, stored client-side). Exactly
    one of user_id/guest_token should be provided by the caller."""
    if user_id is not None:
        cart = await db.scalar(
            select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
        )
        if cart is not None:
            return cart
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart, attribute_names=["items"])
        return cart

    if guest_token is not None:
        cart = await db.scalar(
            select(Cart).where(Cart.guest_token == guest_token).options(selectinload(Cart.items))
        )
        if cart is not None:
            return cart

    new_token = guest_token or generate_guest_token()
    cart = Cart(guest_token=new_token)
    db.add(cart)
    await db.commit()
    await db.refresh(cart, attribute_names=["items"])
    return cart


async def add_item(
    db: AsyncSession, cart: Cart, *, product_id: uuid.UUID, variant_id: uuid.UUID | None, quantity: int
) -> Cart:
    product = await db.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} not found")

    existing = next(
        (i for i in cart.items if i.product_id == product_id and i.variant_id == variant_id), None
    )
    if existing is not None:
        existing.quantity += quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, variant_id=variant_id, quantity=quantity))

    await db.commit()
    await db.refresh(cart, attribute_names=["items"])
    return cart


async def update_item_quantity(db: AsyncSession, cart: Cart, item_id: uuid.UUID, quantity: int) -> Cart:
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        raise ValueError("Cart item not found")
    item.quantity = quantity
    await db.commit()
    await db.refresh(cart, attribute_names=["items"])
    return cart


async def remove_item(db: AsyncSession, cart: Cart, item_id: uuid.UUID) -> Cart:
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is not None:
        await db.delete(item)
        await db.commit()
        await db.refresh(cart, attribute_names=["items"])
    return cart


async def clear_cart(db: AsyncSession, cart: Cart) -> Cart:
    for item in list(cart.items):
        await db.delete(item)
    await db.commit()
    await db.refresh(cart, attribute_names=["items"])
    return cart


async def merge_guest_cart_into_user_cart(db: AsyncSession, *, user_id: uuid.UUID, guest_token: str) -> Cart:
    """On login, the guest cart's items are merged into the user's existing
    cart (quantity-summed for matching product+variant lines), then the
    guest cart row is deleted. Replaces the old app's localStorage-only cart,
    which never needed a merge step since it was never server-persisted."""
    user_cart = await get_or_create_cart(db, user_id=user_id, guest_token=None)
    guest_cart = await db.scalar(
        select(Cart).where(Cart.guest_token == guest_token).options(selectinload(Cart.items))
    )
    if guest_cart is None or guest_cart.id == user_cart.id:
        return user_cart

    for guest_item in guest_cart.items:
        existing = next(
            (i for i in user_cart.items if i.product_id == guest_item.product_id and i.variant_id == guest_item.variant_id),
            None,
        )
        if existing is not None:
            existing.quantity += guest_item.quantity
        else:
            db.add(
                CartItem(
                    cart_id=user_cart.id,
                    product_id=guest_item.product_id,
                    variant_id=guest_item.variant_id,
                    quantity=guest_item.quantity,
                )
            )

    await db.delete(guest_cart)
    await db.commit()
    await db.refresh(user_cart, attribute_names=["items"])
    return user_cart


async def to_cart_out_items(db: AsyncSession, cart: Cart) -> list[dict]:
    """Enriches raw cart items with product display data (name/slug/price/
    image), mirroring the shape the old app's client-side CartItem carried."""
    out = []
    for item in cart.items:
        product = await db.get(Product, item.product_id, options=[selectinload(Product.images)])
        if product is None:
            continue
        variant = await db.get(ProductVariant, item.variant_id) if item.variant_id else None
        unit_price = Decimal(product.base_price_usd) + (Decimal(variant.price_delta_usd) if variant else Decimal(0))
        variant_label = None
        if variant is not None:
            parts = [p for p in (variant.length, variant.color, variant.texture) if p]
            variant_label = " / ".join(parts) if parts else None
        image_url = product.images[0].url if product.images else None
        out.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "unit_price_usd": unit_price,
                "name": product.name,
                "slug": product.slug,
                "image_url": image_url,
                "variant_label": variant_label,
            }
        )
    return out
