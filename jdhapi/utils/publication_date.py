from pickle import FALSE, TRUE
from jdhapi.models import Article
import logging

logger = logging.getLogger(__name__)


def check_if_editorial(pid):
    article = Article.objects.filter(abstract__pid=pid, tags__name="editorial").first()
    if article:
        return True
    else:
        return False


def get_order_publication(pid, issue):
    # Check if editorial
    # logger.info(f"result check if editorial {check_if_editorial(pid)}")
    if check_if_editorial(pid):
        return "1"
    else:
        seq = "UNDEFINED"
        articles = Article.objects.filter(status=Article.Status.PUBLISHED, issue=issue).order_by('publication_date').values("abstract__pid", 'abstract__title')
        for index, article in enumerate(articles, 2):
            # logger.info(f"Articles issue {issue} sorted {article['abstract__title']} - INDEX {index}")
            if pid == article['abstract__pid']:
                seq = index
        return seq





