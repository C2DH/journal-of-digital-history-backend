from django.db.models.signals import pre_save, post_save
from django.core.mail import send_mail
from jdhapi.models import Article
from django.dispatch import receiver
from jdhapi.utils.articleUtils import get_notebook_from_github
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def send_email_for_peer_review_article(sender, instance, created, **kwargs):
    if not created and instance.tracker.has_changed('status') and instance.status == Article.Status.PEER_REVIEW:
        instance.send_email_if_peer_review()

@receiver(pre_save, sender=Article)
def pre_save_article(sender, instance, **kwargs):
    logger.debug("Inside pre_save_article")

    # Check if full_url_article_path has changed
    if instance.tracker.has_changed('full_url_article_path'):
        # Update other fields if necessary
        repository_url, notebook_path, notebook_ipython_url = get_notebook_from_github(instance.full_url_article_path)

        # Set the values directly without calling save
        instance.notebook_ipython_url = notebook_ipython_url
        instance.repository_url = repository_url
        instance.notebook_path = notebook_path

    logger.debug("Fields populated: notebook_ipython_url=%s, repository_url=%s, notebook_path=%s" % (
        instance.notebook_ipython_url, instance.repository_url, instance.notebook_path))