import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_current_user_optional, get_db
from app.core.rate_limit import rate_limit
from app.core.security import (
    create_guest_order_access_token,
    hash_password,
    verify_guest_order_access_token,
)
from app.integrations import bank_transfer, mpesa_daraja
from app.models.catalog import ProductVariant
from app.models.enums import OrderStatus, PaymentProviderType, PaymentStatus
from app.models.identity import User
from app.models.orders import Order, OrderItem, OrderStatusHistory
from app.models.payments import Payment
from app.models.pricing import DiscountCode
from app.schemas.orders import (
    CheckoutRequest,
    CheckoutResponse,
    OrderItemOut,
    OrderListItemOut,
    OrderListOut,
    OrderOut,
    OrderPackageOut,
)
from app.services import cart_breakdown as cart_breakdown_service
from app.services import order_state_machine
from app.services.audit import log_audit
from app.services.exchange_rate import convert_usd_to_kes, get_usd_to_kes_rate
from app.services.order_numbering import generate_order_number
from app.services.pricing_settings import get_pricing_settings
from app.services.tracking_numbering import generate_order_tracking_number

router = APIRouter(prefix="/orders", tags=["orders"])

ORDER_LIST_PAGE_SIZE = 20


@router.post("", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CheckoutResponse:
    is_guest = current_user is None

    # Guest checkout: no session means we auto-create (or reuse) a User row
    # keyed by the email they typed at checkout, so orders always have a real
    # user_id without forcing registration first. An email that already
    # belongs to a registered account just attaches this order to that
    # account rather than erroring or touching their password.
    if current_user is not None:
        user_id = current_user.id
    else:
        if payload.shipping_address.email is None:
            raise HTTPException(status_code=400, detail="Email is required to check out as a guest.")

        if not await rate_limit(f"guest-checkout:{payload.shipping_address.email}", limit=10, window_seconds=600):
            raise HTTPException(status_code=429, detail="Too many checkout attempts. Please wait a few minutes and try again.")

        existing = await db.scalar(select(User).where(User.email == payload.shipping_address.email))
        if existing is not None:
            user_id = existing.id
        else:
            guest_user = User(
                email=payload.shipping_address.email,
                name=payload.shipping_address.full_name,
                phone=payload.shipping_address.phone,
                # Not a usable credential - guests never log in with it.
                password_hash=hash_password(secrets.token_hex(32)),
            )
            db.add(guest_user)
            await db.flush()
            user_id = guest_user.id

    if not await rate_limit(f"create-order:{user_id}", limit=10, window_seconds=600):
        raise HTTPException(status_code=429, detail="Too many checkout attempts. Please wait a few minutes and try again.")

    if payload.payment_method == "MPESA" and not payload.mpesa_phone:
        raise HTTPException(status_code=400, detail="Phone number is required for M-Pesa.")

    if payload.payment_method == "MPESA" and payload.mpesa_phone and not await rate_limit(
        f"stk-push:{payload.mpesa_phone}", limit=3, window_seconds=600
    ):
        raise HTTPException(
            status_code=429, detail="Too many M-Pesa prompts sent to this number recently. Please wait and try again."
        )

    try:
        result = await cart_breakdown_service.calculate_cart_breakdown(
            db,
            [
                cart_breakdown_service.CartLineInput(
                    product_id=item.product_id, variant_id=item.variant_id, quantity=item.quantity
                )
                for item in payload.items
            ],
            payload.shipping_address.country_code,
            payload.discount_code,
        )
    except (cart_breakdown_service.ShippingRuleNotFoundError, cart_breakdown_service.ProductNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    breakdown, resolved_lines, applied_discount = result.breakdown, result.resolved_lines, result.applied_discount

    exchange_rate = await get_usd_to_kes_rate(db)
    settings_for_kes = await get_pricing_settings(db)
    total_amount_kes = convert_usd_to_kes(breakdown.total_amount_usd, exchange_rate, settings_for_kes.kes_adjustment)
    order_number = generate_order_number()
    # Generated once, here, and never regenerated afterwards - see
    # docs/VNKE_ROADMAP.md Phase 3 for why this must happen at order
    # creation rather than whenever a warehouse later touches the package.
    tracking_number = await generate_order_tracking_number(db)

    order = Order(
        order_number=order_number,
        tracking_number=tracking_number,
        user_id=user_id,
        status=OrderStatus.PENDING_PAYMENT,
        subtotal_usd=breakdown.subtotal_usd,
        shipping_fee_usd=breakdown.shipping_fee_usd,
        handling_fee_usd=breakdown.handling_fee_usd,
        customs_estimate_usd=breakdown.customs_estimate_usd,
        discount_code_id=applied_discount.id if applied_discount else None,
        total_amount_usd=breakdown.total_amount_usd,
        exchange_rate_applied=exchange_rate,
        total_amount_kes=total_amount_kes,
        shipping_country=payload.shipping_address.country_code,
        shipping_address=payload.shipping_address.model_dump(mode="json"),
    )
    db.add(order)
    await db.flush()

    for line in resolved_lines:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price_usd_at_purchase=line.unit_price_usd,
                line_total_usd=line.unit_price_usd * line.quantity,
            )
        )
    db.add(OrderStatusHistory(order_id=order.id, to_status=OrderStatus.PENDING_PAYMENT, note="Order created at checkout"))

    # Decrement stock atomically with order creation: a conditional UPDATE
    # that only succeeds if enough stock remains, closing the race where two
    # concurrent checkouts both read sufficient stock before either commits.
    # Lines without a variant have nothing to decrement - stock is only
    # tracked per-variant, never at the product level.
    for line in resolved_lines:
        if line.variant_id is None:
            continue
        stock_update = await db.execute(
            update(ProductVariant)
            .where(ProductVariant.id == line.variant_id, ProductVariant.stock_qty >= line.quantity)
            .values(stock_qty=ProductVariant.stock_qty - line.quantity)
        )
        if stock_update.rowcount == 0:  # type: ignore[attr-defined]
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Not enough stock available for one of the items in your cart. Please adjust the quantity and try again.",
            )

    # Re-check the usage limit inside the transaction to close the race where
    # two concurrent checkouts both passed the earlier "active discount"
    # lookup when only one use was left.
    if applied_discount is not None:
        discount_update = await db.execute(
            update(DiscountCode)
            .where(
                DiscountCode.id == applied_discount.id,
                (DiscountCode.usage_limit.is_(None)) | (DiscountCode.times_used < DiscountCode.usage_limit),
            )
            .values(times_used=DiscountCode.times_used + 1)
        )
        if discount_update.rowcount == 0:  # type: ignore[attr-defined]
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f'Discount code "{applied_discount.code}" has just reached its usage limit. Please remove it and try again.',
            )

    await log_audit(
        db,
        user_id=user_id,
        action="CREATE_ORDER",
        entity_type="Order",
        entity_id=str(order.id),
        metadata={"totalAmountUsd": str(breakdown.total_amount_usd), "paymentMethod": payload.payment_method},
    )
    await db.commit()

    payment_instructions: dict = {}

    if payload.payment_method == "MPESA":
        try:
            stk_result = await mpesa_daraja.stk_push(
                phone=payload.mpesa_phone,  # type: ignore[arg-type]
                amount_kes=total_amount_kes,
                account_reference=str(order.id),
                transaction_desc=f"Hiar Business order {order.id}",
            )
            db.add(
                Payment(
                    order_id=order.id,
                    provider=PaymentProviderType.MPESA,
                    provider_ref=stk_result.CheckoutRequestID,
                    amount_kes=total_amount_kes,
                    status=PaymentStatus.PENDING,
                )
            )
            payment_instructions = {"message": "Check your phone to complete the M-Pesa payment."}
        except Exception as exc:  # noqa: BLE001 - M-Pesa may be unconfigured/unreachable; order still stands
            db.add(
                Payment(
                    order_id=order.id,
                    provider=PaymentProviderType.MPESA,
                    amount_kes=total_amount_kes,
                    status=PaymentStatus.FAILED,
                )
            )
            payment_instructions = {"error": f"M-Pesa is not configured yet in this environment: {exc}"}

            # Basic fraud/abuse signal: repeated failed payment initiations
            # from the same account in a short window get flagged for review.
            if not await rate_limit(f"mpesa-failures:{user_id}", limit=3, window_seconds=1800):
                await log_audit(
                    db,
                    user_id=user_id,
                    action="FRAUD_FLAG_REPEATED_PAYMENT_FAILURES",
                    entity_type="Order",
                    entity_id=str(order.id),
                    metadata={"reason": "3+ failed M-Pesa initiations within 30 minutes"},
                )
        await db.commit()
    else:
        provider_ref = bank_transfer.initiate_bank_transfer(str(order.id))
        db.add(
            Payment(
                order_id=order.id,
                provider=PaymentProviderType.BANK_TRANSFER,
                provider_ref=provider_ref,
                amount_kes=total_amount_kes,
                status=PaymentStatus.INITIATED,
            )
        )
        await db.commit()
        payment_instructions = {"bankDetails": bank_transfer.bank_transfer_details(), "amountKes": str(total_amount_kes)}

    return CheckoutResponse(
        order_number=order.order_number,
        tracking_number=tracking_number,
        payment_instructions=payment_instructions,
        guest_access_token=create_guest_order_access_token(order.order_number) if is_guest else None,
    )


@router.get("", response_model=OrderListOut)
async def list_my_orders(
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderListOut:
    total = await db.scalar(
        select(func.count()).select_from(Order).where(Order.user_id == current_user.id)
    ) or 0
    orders = (
        (
            await db.execute(
                select(Order)
                .where(Order.user_id == current_user.id)
                .order_by(Order.created_at.desc())
                .offset((page - 1) * ORDER_LIST_PAGE_SIZE)
                .limit(ORDER_LIST_PAGE_SIZE)
            )
        )
        .scalars()
        .all()
    )
    return OrderListOut(
        orders=[
            OrderListItemOut(
                order_number=o.order_number, tracking_number=o.tracking_number, status=o.status, currency=o.currency,
                total_amount_usd=o.total_amount_usd, total_amount_kes=o.total_amount_kes, created_at=o.created_at,
            )
            for o in orders
        ],
        total=total,
        page=page,
        page_size=ORDER_LIST_PAGE_SIZE,
    )


@router.get("/{order_number}", response_model=OrderOut)
async def get_order(
    order_number: str,
    guest_token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> OrderOut:
    order = await db.scalar(
        select(Order)
        .where(Order.order_number == order_number)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.packages),
        )
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    is_owner = current_user is not None and current_user.id == order.user_id
    is_valid_guest = guest_token is not None and verify_guest_order_access_token(guest_token, order_number)
    if not is_owner and not is_valid_guest:
        raise HTTPException(status_code=403, detail="You do not have access to this order")

    return OrderOut(
        id=order.id,
        order_number=order.order_number,
        tracking_number=order.tracking_number,
        status=order.status,
        currency=order.currency,
        subtotal_usd=order.subtotal_usd,
        shipping_fee_usd=order.shipping_fee_usd,
        handling_fee_usd=order.handling_fee_usd,
        customs_estimate_usd=order.customs_estimate_usd,
        total_amount_usd=order.total_amount_usd,
        total_amount_kes=order.total_amount_kes,
        shipping_country=order.shipping_country,
        shipping_address=order.shipping_address,
        items=[_order_item_to_out(item) for item in order.items],
        packages=[OrderPackageOut(package_code=p.package_code, status=p.status.value) for p in order.packages],
    )


def _order_item_to_out(item: OrderItem) -> OrderItemOut:
    # variant_label composition mirrors services/cart.py::to_cart_out_items
    # for consistency between the cart and order-detail item displays.
    variant_label = None
    if item.variant is not None:
        parts = [p for p in (item.variant.length, item.variant.color, item.variant.texture) if p]
        variant_label = " / ".join(parts) if parts else None

    return OrderItemOut(
        product_id=item.product_id,
        product_name=item.product.name,
        product_slug=item.product.slug,
        variant_id=item.variant_id,
        variant_label=variant_label,
        quantity=item.quantity,
        unit_price_usd_at_purchase=item.unit_price_usd_at_purchase,
        line_total_usd=item.line_total_usd,
    )


@router.post("/{order_number}/cancel", response_model=OrderOut)
async def cancel_order(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = await db.scalar(select(Order).where(Order.order_number == order_number))
    # 404 (not 403) whether the order doesn't exist or belongs to someone
    # else - same non-leaking convention used by the supplier routers.
    if order is None or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        await order_state_machine.transition_order_status(
            db, order.id, OrderStatus.CANCELLED, actor_user_id=current_user.id, note="Cancelled by customer"
        )
    except order_state_machine.InvalidTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return await get_order(order_number, guest_token=None, db=db, current_user=current_user)
