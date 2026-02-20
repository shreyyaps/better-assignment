from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from app.core.config import Settings
from app.workers.sync_worker import run_polling_sync


def start_email_scheduler(app: Flask) -> BackgroundScheduler:
    settings = Settings()
    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)

    scheduler.add_job(
        func=run_polling_sync,
        trigger="interval",
        minutes=settings.scheduler_interval_minutes,
        id="email_polling_job",
        replace_existing=True,
    )

    # TODO: In multi-worker deployments, this can run in each worker.
    # Consider using a distributed scheduler or a leader election mechanism.
    scheduler.start()

    app.logger.info("Email polling scheduler started")
    return scheduler


def stop_email_scheduler(scheduler: BackgroundScheduler) -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
