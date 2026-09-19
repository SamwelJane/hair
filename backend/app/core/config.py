from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, replacing the scattered process.env reads
    across the old src/lib/** modules with one typed source."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hiar_business"
    redis_url: str = "redis://localhost:6379"

    jwt_secret: str = "change-me-in-env-this-default-is-not-secure-do-not-ship-it"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    resend_api_key: str | None = None
    email_from: str = "orders@hiarbusiness.com"

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str = "whatsapp:+254712197226"

    mpesa_env: str = "sandbox"
    mpesa_consumer_key: str | None = None
    mpesa_consumer_secret: str | None = None
    mpesa_shortcode: str | None = None
    mpesa_passkey: str | None = None
    mpesa_callback_url: str | None = None

    bank_transfer_bank_name: str | None = None
    bank_transfer_account_name: str | None = None
    bank_transfer_account_number: str | None = None
    bank_transfer_swift_code: str | None = None

    admin_notification_email: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5180"]
    frontend_url: str = "http://localhost:5173"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["http://localhost:5173", "http://localhost:5180"]

    # Contabo / PostgreSQL Connection Pool & WAN Keepalive settings
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800
    db_pool_timeout: int = 30

    # Meta WhatsApp Business Cloud API
    meta_whatsapp_token: str | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_verify_token: str = "hiar-meta-verify-token"
    meta_whatsapp_business_account_id: str | None = None

    # Equity Bank Kenya payment configuration
    equity_paybill: str = "247247"
    equity_account_number: str = "0310173604563"
    equity_account_name: str = "Cherubim Express Ltd"

    # Exchange Rate API (optional key for premium provider)
    exchange_rate_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
