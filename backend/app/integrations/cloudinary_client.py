import logging

import cloudinary
import cloudinary.uploader

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Shared by every product-image upload path (admin and supplier) so the cap
# can never drift between the two surfaces.
MAX_PRODUCT_IMAGES = 3

_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )
    _configured = True


def upload_image(file_bytes: bytes, folder: str = "hiar-business/products") -> tuple[str, str]:
    """Returns (secure_url, public_id). Raises if Cloudinary isn't
    configured or the upload fails - unlike notifications, a missing image
    upload should surface as an error, not silently no-op."""
    if not settings.cloudinary_cloud_name:
        raise RuntimeError("Cloudinary is not configured (CLOUDINARY_CLOUD_NAME unset).")

    _ensure_configured()
    result = cloudinary.uploader.upload(file_bytes, folder=folder)
    return result["secure_url"], result["public_id"]


def delete_image(public_id: str) -> None:
    """New vs. the old app: deleting a ProductImage row there never cleaned
    up the actual Cloudinary asset (orphaned blobs). Failures here are
    logged, not raised - a stuck-but-orphaned Cloudinary asset is a cleanup
    nuisance, not a reason to fail the delete-image request the admin made."""
    if not settings.cloudinary_cloud_name:
        return
    _ensure_configured()
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:  # noqa: BLE001 - see docstring; failure here must not block the DB delete
        logger.warning("Failed to delete Cloudinary asset %s - continuing", public_id)
