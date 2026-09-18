from typing import ClassVar

from app.core.logging import configure_logging
from app.worker.pool import redis_settings
from app.worker.tasks import notify_supplier_new_order, notify_supplier_status_change

configure_logging()


class WorkerSettings:
    """arq worker entrypoint. Run with: arq app.worker.worker.WorkerSettings

    Chosen over Celery given this app's actual job volume (supplier email/
    WhatsApp notifications only) - see the migration plan's background-jobs
    section for the reasoning. Requires the persistent-server deploy target
    (confirmed) rather than the old app's serverless cron-drain pattern."""

    functions: ClassVar = [notify_supplier_new_order, notify_supplier_status_change]
    redis_settings = redis_settings()
