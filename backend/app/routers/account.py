from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.identity import User
from app.schemas.account import (
    AccountExportOrderItemOut,
    AccountExportOrderOut,
    AccountExportOut,
    AccountExportPaymentOut,
    AccountExportReviewOut,
    AccountExportStatusHistoryOut,
    AccountExportUserOut,
)
from app.schemas.addresses import AddressOut
from app.services import account as account_service
from app.services.users import deactivate_own_account

router = APIRouter(prefix="/account", tags=["account"], dependencies=[Depends(get_current_user)])


@router.get("/export")
async def export_my_account_data(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> JSONResponse:
    orders = await account_service.list_own_orders_with_details(db, user.id)
    addresses = await account_service.list_own_addresses(db, user.id)
    reviews = await account_service.list_own_reviews(db, user.id)

    export = AccountExportOut(
        user=AccountExportUserOut(
            id=user.id, email=user.email, name=user.name, phone=user.phone, role=user.role,
            created_at=user.created_at,
        ),
        orders=[
            AccountExportOrderOut(
                order_number=o.order_number, status=o.status, currency=o.currency,
                total_amount_usd=o.total_amount_usd, total_amount_kes=o.total_amount_kes, created_at=o.created_at,
                items=[
                    AccountExportOrderItemOut(
                        product_id=i.product_id, variant_id=i.variant_id, quantity=i.quantity,
                        unit_price_usd_at_purchase=i.unit_price_usd_at_purchase, line_total_usd=i.line_total_usd,
                    )
                    for i in o.items
                ],
                payments=[
                    AccountExportPaymentOut(
                        id=p.id, provider=p.provider, provider_ref=p.provider_ref, amount_kes=p.amount_kes,
                        status=p.status, created_at=p.created_at,
                    )
                    for p in o.payments
                ],
                status_history=[
                    AccountExportStatusHistoryOut(
                        from_status=h.from_status, to_status=h.to_status, note=h.note, created_at=h.created_at
                    )
                    for h in o.status_history
                ],
            )
            for o in orders
        ],
        addresses=[
            AddressOut(
                id=a.id, label=a.label, full_name=a.full_name, line1=a.line1, line2=a.line2, city=a.city,
                country_code=a.country_code, postal_code=a.postal_code, phone=a.phone, is_default=a.is_default,
            )
            for a in addresses
        ],
        reviews=[
            AccountExportReviewOut(
                id=r.id, product_id=r.product_id, order_id=r.order_id, rating=r.rating, body=r.body,
                status=r.status, created_at=r.created_at,
            )
            for r in reviews
        ],
        exported_at=datetime.now(UTC),
    )

    return JSONResponse(
        content=export.model_dump(mode="json"),
        headers={"Content-Disposition": 'attachment; filename="my-hiar-business-data.json"'},
    )


@router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_my_account(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    await deactivate_own_account(db, user)
