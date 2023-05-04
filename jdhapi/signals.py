from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from jdhapi.models import Article


@receiver(post_save, sender=Article)
def send_email_for_peer_review_article(sender, instance, created, **kwargs):
    if not created and instance.tracker.has_changed('status') and instance.status == Article.Status.PEER_REVIEW:
        instance.send_email_if_peer_review()
