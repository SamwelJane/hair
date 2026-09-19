import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consolidation import Consolidation
from app.models.customs import CustomsDeclaration
from app.models.enums import (
    ConsolidationStatus,
    CustomsStatus,
    OpsExceptionSeverity,
    OpsExceptionStatus,
    OpsExceptionType,
    PackageStatus,
)
from app.models.exceptions import OpsException
from app.models.external_shipments import ExternalShipment
from app.models.orders import Order
from app.models.packages import Package
from app.services.audit import log_audit
from app.services.notifications.whatsapp import (
    customer_customs_cleared_whatsapp_message,
    send_whatsapp,
)
from app.services.tracking_events import add_event


class CustomsDeclarationNotFoundError(Exception):
    pass


class InvalidCustomsTransitionError(Exception):
    pass


async def declare(
    db: AsyncSession,
    *,
    declaration_id: uuid.UUID,
    hs_code: str,
    declared_value_usd: Decimal,
    duty_usd: Decimal,
    vat_usd: Decimal,
    actor_user_id: uuid.UUID,
) -> CustomsDeclaration:
    declaration = await db.get(CustomsDeclaration, declaration_id)
    if declaration is None:
        raise CustomsDeclarationNotFoundError(f"Customs declaration {declaration_id} not found.")
    if declaration.status != CustomsStatus.PREPARING:
        raise InvalidCustomsTransitionError(f"Cannot declare from status {declaration.status.value}.")

    declaration.hs_code = hs_code
    declaration.declared_value_usd = declared_value_usd
    declaration.duty_usd = duty_usd
    declaration.vat_usd = vat_usd
    declaration.status = CustomsStatus.DECLARED

    await log_audit(
        db,
        user_id=actor_user_id,
        action="CUSTOMS_DECLARED",
        entity_type="CustomsDeclaration",
        entity_id=str(declaration.id),
        metadata={"hsCode": hs_code, "declaredValueUsd": str(declared_value_usd)},
    )
    await db.commit()
    await db.refresh(declaration)
    return declaration


async def raise_query(db: AsyncSession, *, declaration_id: uuid.UUID, note: str, actor_user_id: uuid.UUID) -> CustomsDeclaration:
    declaration = await db.get(CustomsDeclaration, declaration_id)
    if declaration is None:
        raise CustomsDeclarationNotFoundError(f"Customs declaration {declaration_id} not found.")
    if declaration.status != CustomsStatus.DECLARED:
        raise InvalidCustomsTransitionError(f"Cannot raise a query from status {declaration.status.value}.")

    declaration.status = CustomsStatus.QUERY_RAISED
    declaration.notes = note

    db.add(
        OpsException(
            type=OpsExceptionType.CUSTOMS_QUERY,
            severity=OpsExceptionSeverity.HIGH,
            entity_type="CustomsDeclaration",
            entity_id=str(declaration.id),
            description=note,
            status=OpsExceptionStatus.OPEN,
        )
    )
    await log_audit(
        db,
        user_id=actor_user_id,
        action="CUSTOMS_QUERY_RAISED",
        entity_type="CustomsDeclaration",
        entity_id=str(declaration.id),
        metadata={"note": note},
    )
    await db.commit()
    await db.refresh(declaration)
    return declaration


async def _notify_customs_cleared(db: AsyncSession, packages: list[Package]) -> None:
    """One WhatsApp message per unique order/external shipment, even when a
    consolidation contains several packages for the same owner."""
    notified_order_ids: set[uuid.UUID] = set()
    notified_shipment_ids: set[uuid.UUID] = set()
    for package in packages:
        if package.order_id is not None and package.order_id not in notified_order_ids:
            notified_order_ids.add(package.order_id)
            order = await db.get(Order, package.order_id, options=[selectinload(Order.user)])
            if order is not None:
                phone = (order.shipping_address or {}).get("phone") if isinstance(order.shipping_address, dict) else None
                if not phone and order.user:
                    phone = order.user.phone
                if phone:
                    await send_whatsapp(
                        phone,
                        customer_customs_cleared_whatsapp_message(
                            order_number=order.order_number, tracking_number=order.tracking_number
                        ),
                    )
        elif package.external_shipment_id is not None and package.external_shipment_id not in notified_shipment_ids:
            notified_shipment_ids.add(package.external_shipment_id)
            shipment = await db.get(ExternalShipment, package.external_shipment_id)
            if shipment is not None and shipment.customer_phone:
                await send_whatsapp(
                    shipment.customer_phone,
                    customer_customs_cleared_whatsapp_message(
                        order_number=shipment.tracking_number, tracking_number=shipment.tracking_number
                    ),
                )


async def clear(db: AsyncSession, *, declaration_id: uuid.UUID, actor_user_id: uuid.UUID) -> CustomsDeclaration:
    """Clearing closes the loop: the consolidation (if this declaration is
    at the batch level) moves to CLOSED and every member package advances
    to READY_FOR_DELIVERY - the last status this roadmap manages, since
    Kenya last-mile delivery (Phase 8) is out of scope."""
    declaration = await db.get(CustomsDeclaration, declaration_id)
    if declaration is None:
        raise CustomsDeclarationNotFoundError(f"Customs declaration {declaration_id} not found.")
    if declaration.status not in (CustomsStatus.DECLARED, CustomsStatus.QUERY_RAISED):
        raise InvalidCustomsTransitionError(f"Cannot clear from status {declaration.status.value}.")

    declaration.status = CustomsStatus.CLEARED
    advanced_packages: list[Package] = []

    if declaration.consolidation_id is not None:
        consolidation = await db.get(
            Consolidation, declaration.consolidation_id, options=[selectinload(Consolidation.packages)]
        )
        if consolidation is not None:
            consolidation.status = ConsolidationStatus.CLOSED
            for package in consolidation.packages:
                package.status = PackageStatus.READY_FOR_DELIVERY
                await add_event(db, package_id=package.id, label="Ready for Delivery", actor_user_id=actor_user_id)
                advanced_packages.append(package)
    elif declaration.package_id is not None:
        single_package = await db.get(Package, declaration.package_id)
        if single_package is not None:
            single_package.status = PackageStatus.READY_FOR_DELIVERY
            await add_event(db, package_id=single_package.id, label="Ready for Delivery", actor_user_id=actor_user_id)
            advanced_packages.append(single_package)

    await log_audit(
        db, user_id=actor_user_id, action="CUSTOMS_CLEARED", entity_type="CustomsDeclaration",
        entity_id=str(declaration.id), metadata={},
    )
    await db.commit()
    await db.refresh(declaration)

    await _notify_customs_cleared(db, advanced_packages)

    return declaration
