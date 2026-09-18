from sqlalchemy import select

from app.models.enums import OrderStatus, PaymentStatus
from app.models.orders import Order, OrderStatusHistory
from app.models.payments import Payment
from tests.integration.conftest import checkout_payload


async def _create_order_via_checkout(client, product, variant):
    resp = await client.post("/orders", json=checkout_payload(product.id, variant.id))
    assert resp.status_code == 201
    return resp.json()["order_number"]


async def _login_admin(client, admin_user, password="adminpass1") -> str:
    resp = await client.post("/auth/login", json={"email": admin_user.email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_strict_admin_can_confirm_bank_transfer_payment(client, db, checkout_fixtures, admin_user):
    order_number = await _create_order_via_checkout(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    token = await _login_admin(client, admin_user)
    resp = await client.post(
        "/payments/bank-transfer/confirm", json={"payment_id": str(payment.id)}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    await db.refresh(payment)
    await db.refresh(order)
    assert payment.status == PaymentStatus.SUCCESS
    assert order.status == OrderStatus.PAID


async def test_non_admin_cannot_confirm_bank_transfer_payment(client, db, checkout_fixtures):
    order_number = await _create_order_via_checkout(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    register_resp = await client.post(
        "/auth/register", json={"name": "Customer", "email": "customer@example.com", "password": "supersecret1"}
    )
    token = register_resp.json()["access_token"]

    resp = await client.post(
        "/payments/bank-transfer/confirm", json={"payment_id": str(payment.id)}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


async def test_staff_role_cannot_confirm_payment_only_strict_admin_can(client, db, checkout_fixtures):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.identity import User

    staff = User(email="staff@example.com", name="Staff", password_hash=hash_password("staffpass1"), role=UserRole.STAFF)
    db.add(staff)
    await db.commit()

    order_number = await _create_order_via_checkout(client, checkout_fixtures["product"], checkout_fixtures["variant"])
    order = (await db.execute(select(Order).where(Order.order_number == order_number))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    login_resp = await client.post("/auth/login", json={"email": "staff@example.com", "password": "staffpass1"})
    token = login_resp.json()["access_token"]

    resp = await client.post(
        "/payments/bank-transfer/confirm", json={"payment_id": str(payment.id)}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


async def test_confirming_non_bank_transfer_payment_rejected(client, db, admin_user, checkout_fixtures):
    payload = checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    payload["payment_method"] = "MPESA"
    payload["mpesa_phone"] = "+254711111111"
    resp = await client.post("/orders", json=payload)
    assert resp.status_code == 201
    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    token = await _login_admin(client, admin_user)
    confirm_resp = await client.post(
        "/payments/bank-transfer/confirm", json={"payment_id": str(payment.id)}, headers={"Authorization": f"Bearer {token}"}
    )
    assert confirm_resp.status_code == 400


async def test_mpesa_callback_marks_payment_success_and_order_paid(client, db, checkout_fixtures):
    payload = checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    payload["payment_method"] = "MPESA"
    payload["mpesa_phone"] = "+254711111111"
    resp = await client.post("/orders", json=payload)
    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()

    # Since M-Pesa isn't configured in tests, checkout marks the payment
    # FAILED already (no Daraja credentials) - simulate the provider_ref a
    # real STK push would have set, so the callback lookup can find it.
    payment.provider_ref = "ws_CO_test123"
    payment.status = payment.status.__class__.PENDING
    await db.commit()

    callback_body = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "mr-1",
                "CheckoutRequestID": "ws_CO_test123",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {"Item": [{"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"}]},
            }
        }
    }
    callback_resp = await client.post("/payments/mpesa/callback", json=callback_body)
    assert callback_resp.status_code == 200
    assert callback_resp.json()["ResultCode"] == 0

    await db.refresh(payment)
    await db.refresh(order)
    assert payment.status == PaymentStatus.SUCCESS
    assert payment.provider_ref == "NLJ7RT61SV"
    assert order.status == OrderStatus.PAID


async def test_mpesa_callback_unknown_checkout_request_id_acknowledged_without_error(client):
    callback_body = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "mr-1",
                "CheckoutRequestID": "does-not-exist",
                "ResultCode": 0,
                "ResultDesc": "ok",
            }
        }
    }
    resp = await client.post("/payments/mpesa/callback", json=callback_body)
    assert resp.status_code == 200
    assert resp.json()["ResultCode"] == 0


async def test_mpesa_callback_is_idempotent_on_replay(client, db, checkout_fixtures):
    payload = checkout_payload(checkout_fixtures["product"].id, checkout_fixtures["variant"].id)
    payload["payment_method"] = "MPESA"
    payload["mpesa_phone"] = "+254711111111"
    resp = await client.post("/orders", json=payload)
    order = (await db.execute(select(Order).where(Order.order_number == resp.json()["order_number"]))).scalar_one()
    payment = (await db.execute(select(Payment).where(Payment.order_id == order.id))).scalar_one()
    payment.provider_ref = "ws_CO_replay"
    payment.status = PaymentStatus.PENDING
    await db.commit()

    callback_body = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "mr-1",
                "CheckoutRequestID": "ws_CO_replay",
                "ResultCode": 0,
                "ResultDesc": "ok",
            }
        }
    }
    first = await client.post("/payments/mpesa/callback", json=callback_body)
    assert first.status_code == 200

    history_after_first = (
        await db.execute(select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id))
    ).scalars().all()

    # A second, replayed callback for an already-SUCCESS payment must be a
    # no-op (idempotency guard), not double-apply the status transition.
    second = await client.post("/payments/mpesa/callback", json=callback_body)
    assert second.status_code == 200

    history_after_second = (
        await db.execute(select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id))
    ).scalars().all()

    await db.refresh(payment)
    assert payment.status == PaymentStatus.SUCCESS
    assert len(history_after_second) == len(history_after_first)
