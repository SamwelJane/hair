import re
from decimal import Decimal

import pytest

from app.core.security import hash_password
from app.models.enums import OrderStatus
from app.models.external_shipments import ExternalShipment
from app.models.identity import User
from app.models.orders import Order
from app.services import tracking_numbering
from app.services.tracking_numbering import (
    TrackingNumberGenerationError,
    generate_external_shipment_tracking_number,
    generate_order_tracking_number,
)

_DATE_RE = r"\d{8}"


async def test_order_tracking_number_format(db):
    tracking_number = await generate_order_tracking_number(db)
    assert re.fullmatch(rf"VNKE-{_DATE_RE}-[A-Z0-9]{{6}}", tracking_number)


async def test_external_shipment_tracking_number_format(db):
    tracking_number = await generate_external_shipment_tracking_number(db)
    assert re.fullmatch(rf"VNKE-EXT-{_DATE_RE}-[A-Z0-9]{{6}}", tracking_number)


async def test_generator_retries_on_collision_then_succeeds(db, monkeypatch):
    taken = await generate_external_shipment_tracking_number(db)
    db.add(ExternalShipment(tracking_number=taken, customer_name="Jane", customer_phone="+254700000000"))
    await db.commit()

    # Force the first candidate to exactly match the already-taken number's
    # suffix so the collision path is actually exercised, not just luck.
    taken_suffix = taken.rsplit("-", 1)[1]
    suffixes = iter([taken_suffix, "FRESH1"])
    monkeypatch.setattr(tracking_numbering, "random_suffix", lambda length: next(suffixes)[:length])

    result = await generate_external_shipment_tracking_number(db)
    assert result != taken


async def test_generator_gives_up_after_five_attempts(db, monkeypatch):
    taken = await generate_order_tracking_number(db)
    user = User(email="collision@example.com", name="Collision", password_hash=hash_password("password1"))
    db.add(user)
    await db.flush()
    db.add(
        Order(
            order_number="ORD-COLLISION",
            tracking_number=taken,
            user_id=user.id,
            status=OrderStatus.PENDING_PAYMENT,
            subtotal_usd=Decimal("10.00"),
            shipping_fee_usd=Decimal(0),
            total_amount_usd=Decimal("10.00"),
            shipping_country="KE",
            shipping_address={},
        )
    )
    await db.commit()

    taken_suffix = taken.rsplit("-", 1)[1]
    monkeypatch.setattr(tracking_numbering, "random_suffix", lambda length: taken_suffix[:length])

    with pytest.raises(TrackingNumberGenerationError):
        await generate_order_tracking_number(db)


async def test_order_and_external_shipment_tracking_numbers_share_one_uniqueness_namespace(db):
    """An Order's tracking number must also block an ExternalShipment (and
    vice versa) even though the two prefixes can never actually collide as
    strings today - see tracking_numbering._is_taken."""
    user = User(email="owner@example.com", name="Owner", password_hash=hash_password("password1"))
    db.add(user)
    await db.flush()
    order_tracking_number = "VNKE-20260101-AAAAAA"
    db.add(
        Order(
            order_number="ORD-NAMESPACE-TEST",
            tracking_number=order_tracking_number,
            user_id=user.id,
            status=OrderStatus.PENDING_PAYMENT,
            subtotal_usd=Decimal("10.00"),
            shipping_fee_usd=Decimal(0),
            total_amount_usd=Decimal("10.00"),
            shipping_country="KE",
            shipping_address={},
        )
    )
    await db.commit()

    assert await tracking_numbering._is_taken(db, order_tracking_number) is True
    assert await tracking_numbering._is_taken(db, "VNKE-20260101-ZZZZZZ") is False
