import logging

from app.core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Without this, every logger.warning()/logger.exception() call already
    scattered through app/services/notifications, app/worker, and
    app/integrations (all fail-open external-integration code, deliberately
    logging rather than raising) only reaches Python's unformatted "handler
    of last resort" - no timestamp, no logger name, and DEBUG/INFO never
    shown at all. Called once at process startup, by both the API app
    (app/main.py) and the arq worker (app/worker/worker.py), so operational
    warnings are actually visible in whatever the deploy platform collects
    from stdout/stderr."""
    logging.basicConfig(
        level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
