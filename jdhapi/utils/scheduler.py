import logging
from datetime import timezone

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_background_scheduler = None


def get_background_scheduler():
    global _background_scheduler
    if _background_scheduler is None or not getattr(
        _background_scheduler, "running", False
    ):
        _background_scheduler = BackgroundScheduler(
            timezone=timezone.utc,
            executors={"default": ThreadPoolExecutor(max_workers=3)},
            job_defaults={"coalesce": False, "max_instances": 3},
        )
        _background_scheduler.start()
        logger.info("Background scheduler started")
    return _background_scheduler


def make_listener(total_jobs, scheduler):
    """ Listener to shutdown scheduler when all jobs completed"""
    count = {"remaining": total_jobs}

    def listener(event):
        if event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR):
            count["remaining"] -= 1
            if count["remaining"] <= 0:
                logger.info("All scheduled jobs for this campaign finished.")
                # leave global scheduler running

    return listener
