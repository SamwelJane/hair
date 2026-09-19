from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import (
    account,
    addresses,
    auth,
    cart,
    homepage,
    orders,
    payments,
    pricing,
    products,
    returns,
    reviews,
    tracking,
)
from app.routers.admin import analytics as admin_analytics
from app.routers.admin import audit_logs as admin_audit_logs
from app.routers.admin import categories as admin_categories
from app.routers.admin import homepage as admin_homepage
from app.routers.admin import orders as admin_orders
from app.routers.admin import payments as admin_payments
from app.routers.admin import products as admin_products
from app.routers.admin import promotions as admin_promotions
from app.routers.admin import returns as admin_returns
from app.routers.admin import reviews as admin_reviews
from app.routers.admin import settings as admin_settings
from app.routers.admin import suppliers as admin_suppliers
from app.routers.admin import users as admin_users
from app.routers.supplier import orders as supplier_orders
from app.routers.supplier import products as supplier_products
from app.routers.supplier import promotions as supplier_promotions
from app.routers.warehouse import consolidations as warehouse_consolidations
from app.routers.warehouse import customs as warehouse_customs
from app.routers.warehouse import dashboard as warehouse_dashboard
from app.routers.warehouse import external_shipments as warehouse_external_shipments
from app.routers.warehouse import packages as warehouse_packages
from app.routers.webhooks import mpesa as webhook_mpesa
from app.routers.webhooks import whatsapp as webhook_whatsapp

settings = get_settings()
configure_logging()

app = FastAPI(title="Hiar Business API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(pricing.router)
app.include_router(products.router)
app.include_router(homepage.router)
app.include_router(tracking.router)
app.include_router(addresses.router)
app.include_router(reviews.router)
app.include_router(returns.router)
app.include_router(account.router)
app.include_router(admin_orders.router)
app.include_router(admin_payments.router)
app.include_router(admin_products.router)
app.include_router(admin_categories.router)
app.include_router(admin_homepage.router)
app.include_router(admin_suppliers.router)
app.include_router(admin_returns.router)
app.include_router(admin_reviews.router)
app.include_router(admin_settings.router)
app.include_router(admin_users.router)
app.include_router(admin_audit_logs.router)
app.include_router(admin_analytics.router)
app.include_router(supplier_orders.router)
app.include_router(supplier_products.router)
app.include_router(supplier_promotions.router)
app.include_router(admin_promotions.router)
app.include_router(warehouse_external_shipments.router)
app.include_router(warehouse_packages.router)
app.include_router(warehouse_consolidations.router)
app.include_router(warehouse_customs.router)
app.include_router(warehouse_dashboard.router)
app.include_router(webhook_whatsapp.router)
app.include_router(webhook_mpesa.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
