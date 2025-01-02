from pickle import FALSE, TRUE
from jdhapi.models import Article
import logging

logger = logging.getLogger(__name__)


def check_if_editorial(pid):
    try:
        article = Article.objects.filter(abstract__pid=pid, tags__name="editorial").first()
        if article:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"An error occurred while checking if editorial: {e}")
        return False


def get_order_publication(pid, issue_pid):
    """
    Determine the order of publication for a given article within an issue.

    This function checks if the article is an editorial. If it is, it returns "1".
    Otherwise, it retrieves all published articles in the specified issue, excluding
    editorials, and orders them by their publication date. It then determines the
    position of the given article (identified by `pid`) within this ordered list.

    Args:
        pid (str): The unique identifier of the article.
        issue (str): The identifier of the issue in which the article is published.

    Returns:
        str: The order of publication as a string. Returns "1" if the article is an
             editorial, otherwise returns the position of the article in the ordered
             list or "UNDEFINED" if the article is not found.
    """
    try:
        # Check if editorial
        # logger.info(f"result check if editorial {check_if_editorial(pid)}")
        if check_if_editorial(pid):
            return "1"
        else:
            seq = "UNDEFINED"
            articles = Article.objects.filter(status=Article.Status.PUBLISHED, issue__pid=issue_pid).exclude(tags__name="editorial").order_by('publication_date').values("abstract__pid", 'abstract__title')
            # Start index from 2 because editorials are given the position 1
            for index, article in enumerate(articles, 2):
                logger.info(f"Articles issue {issue_pid} sorted {article['abstract__title']} - INDEX {index}")
                seq = str(index)
            return seq
    except Exception as e:
        logger.error(f"An error occurred while determining the order of publication: {e}")
        return "UNDEFINED"





