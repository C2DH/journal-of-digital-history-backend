# Create your tasks here

from celery import shared_task
from jdhapi.models import Abstract
from django.core.mail import send_mail
from celery.utils.log import get_task_logger
from .models import Article
from jdhapi.utils.articleUtils import get_notebook_stats, get_notebook_specifics_tags, get_citation, generate_tags, generate_narrative_tags, get_notebook_references_fulltext

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
    try:
        send_mail("test subject", "test body", 'jdh.admin@uni.lu', ['elisabeth.guerard@uni.lu'], fail_silently=False,)
    except Exception as e:  # catch *all* exceptions
        logger.error(f'send_confirmation exception:{e}')


@shared_task
def save_article_fingerprint(article_id):
    logger.info(f'save_article_fingerprint article_id:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_fingerprint article_id:{article_id} not found')
    fingerprint = get_notebook_stats(raw_url=article.notebook_ipython_url)
    article.fingerprint = fingerprint
    article.save()


@shared_task
def save_article_specific_content(article_id):
    logger.info(f'save_article_specific_content:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_specific_content:{article_id} not found')
    data = get_notebook_specifics_tags(article, raw_url=article.notebook_ipython_url)
    article.data = data
    article.save()


@shared_task
def save_citation(article_id):
    logger.info(f'save_article_citation:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_citation:{article_id} not found')
    citation = get_citation(raw_url=article.notebook_ipython_url, article=article)
    article.citation = citation
    article.save()


@shared_task
def save_libraries(article_id):
    logger.info(f'save_article_libraries:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_citation:{article_id} not found')
    feedback_tool = generate_tags(article=article)
    feedback_narrative = generate_narrative_tags(article=article)
    logger.info(feedback_tool)
    logger.info(feedback_narrative)



@shared_task
def save_references(article_id):
    logger.info(f'save_article_references:{article_id}')
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        logger.error(f'save_article_references:{article_id} not found')
    logger.info("inside save_article_references")
    references, bibliography, refs = get_notebook_references_fulltext(article_id,raw_url=article.notebook_ipython_url)
    #logger.info(f'References {references}')
    logger.info(f'ok finish')

