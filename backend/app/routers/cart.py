import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_user_optional, get_db
from app.models.cart import Cart
from app.models.identity import User
from app.schemas.cart import (
    AddCartItemRequest,
    CartItemOut,
    CartOut,
    MergeGuestCartRequest,
    UpdateCartItemRequest,
)
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["cart"])

GUEST_CART_HEADER = "X-Guest-Cart-Token"


async def _resolve_cart(
    response: Response,
    x_guest_cart_token: str | None = Header(default=None, alias=GUEST_CART_HEADER),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> Cart:
    cart = await cart_service.get_or_create_cart(
        db, user_id=current_user.id if current_user else None, guest_token=x_guest_cart_token
    )
    if current_user is None and cart.guest_token:
        # Echo back the (possibly newly minted) guest token so the client can
        # persist it and send it on every subsequent cart request.
        response.headers[GUEST_CART_HEADER] = cart.guest_token
    return cart


async def _to_out(db: AsyncSession, cart: Cart) -> CartOut:
    items = await cart_service.to_cart_out_items(db, cart)
    return CartOut(id=cart.id, guest_token=cart.guest_token, items=[CartItemOut(**item) for item in items])


@router.get("", response_model=CartOut)
async def get_cart(cart: Cart = Depends(_resolve_cart), db: AsyncSession = Depends(get_db)) -> CartOut:
    return await _to_out(db, cart)


@router.post("/items", response_model=CartOut, status_code=201)
async def add_cart_item(
    payload: AddCartItemRequest, cart: Cart = Depends(_resolve_cart), db: AsyncSession = Depends(get_db)
) -> CartOut:
    try:
        cart = await cart_service.add_item(
            db, cart, product_id=payload.product_id, variant_id=payload.variant_id, quantity=payload.quantity
        )
    except cart_service.ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _to_out(db, cart)


@router.patch("/items/{item_id}", response_model=CartOut)
async def update_cart_item(
    item_id: uuid.UUID,
    payload: UpdateCartItemRequest,
    cart: Cart = Depends(_resolve_cart),
    db: AsyncSession = Depends(get_db),
) -> CartOut:
    try:
        cart = await cart_service.update_item_quantity(db, cart, item_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await _to_out(db, cart)


@router.delete("/items/{item_id}", response_model=CartOut)
async def remove_cart_item(
    item_id: uuid.UUID, cart: Cart = Depends(_resolve_cart), db: AsyncSession = Depends(get_db)
) -> CartOut:
    cart = await cart_service.remove_item(db, cart, item_id)
    return await _to_out(db, cart)


@router.delete("", response_model=CartOut)
async def clear_cart(cart: Cart = Depends(_resolve_cart), db: AsyncSession = Depends(get_db)) -> CartOut:
    cart = await cart_service.clear_cart(db, cart)
    return await _to_out(db, cart)


@router.post("/merge", response_model=CartOut)
async def merge_guest_cart(
    payload: MergeGuestCartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartOut:
    cart = await cart_service.merge_guest_cart_into_user_cart(
        db, user_id=current_user.id, guest_token=payload.guest_token
    )
    return await _to_out(db, cart)
