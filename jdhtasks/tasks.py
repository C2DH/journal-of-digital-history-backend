import logging
from .celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True)
def echo(self, message):
    logger.info(f'Your message received: {message}')
