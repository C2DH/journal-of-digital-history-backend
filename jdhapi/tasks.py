# Create your tasks here

from celery import shared_task
from jdhapi.models import Abstract
from django.core.mail import send_mail
from celery.utils.log import get_task_logger
from .models import Article
from jdhapi.utils.models import get_notebook_stats

logger = get_task_logger(__name__)


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def count_abstracts():
    return Abstract.objects.count()


@shared_task
def send_confirmation():
    send_mail(
            "test subject",
            "test body",
            'jdh.admin@uni.lu',
            ['elisabeth.guerard@uni.lu'],
            fail_silently=False,
        )


@shared_task
def save_article_fingerprint(article_id):
    logger.info(f'save_article_fingerprint article_id:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_fingerprint article_id:{article_id} not found')
    fingerprint = get_notebook_stats(repository_url=article.repository_url)
    article.data.update({'fingerprint': fingerprint})
    article.save()
