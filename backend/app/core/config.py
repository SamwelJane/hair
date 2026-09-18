from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
