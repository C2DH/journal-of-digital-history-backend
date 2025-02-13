import requests

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from jdhapi.models import Article


@receiver(post_save, sender=Article)
def send_email_for_peer_review_article(sender, instance, created, **kwargs):
    if (
        not created
        and instance.tracker.has_changed("status")
        and instance.status == Article.Status.PEER_REVIEW
    ):
        instance.send_email_if_peer_review()


@receiver(pre_save, sender=Article)
def validate_urls_for_article_submission(sender, instance, **kwargs):
    def check_github_url(url):
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                return False
        return True

    def check_notebook_url(pk):
        if pk:
            article = Article.objects.get(pk=instance.pk)
            db_notebook_url = article.notebook_url
        else:
            db_notebook_url = None
        return db_notebook_url

    if instance.notebook_url != check_notebook_url(instance.pk):
        raise ValidationError("Notebook URL is not correct")

    if instance.notebook_url and check_github_url(instance.repository_url):
        raise ValidationError("Repository url is not correct")
