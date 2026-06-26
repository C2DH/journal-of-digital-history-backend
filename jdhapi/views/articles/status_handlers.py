import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from jdhapi.utils.articles import save_citation

logger = logging.getLogger(__name__)

class StatusHandler:
    def handle(self, article, request):
        raise NotImplementedError

class TechnicalReviewHandler(StatusHandler):
    def handle(self, article, request): 
        logger.info("Setting status TECHNICAL_REVIEW pid=%s", article.abstract.pid)
        article.status = article.Status.TECHNICAL_REVIEW
        article.save()
        return Response({"status": "TECHNICAL_REVIEW set", "article pid": article.abstract.pid})

class CopyEditingHandler(StatusHandler):
    def handle(self, article, request):
        logger.info("Starting COPY_EDITING flow pid=%s", article.abstract.pid)

        article.status = article.Status.COPY_EDITING
        article.save()
        logger.info("Set status COPY_EDITING pid=%s", article.abstract.pid)
        return Response({"status": "COPY_EDITING set", "article pid": article.abstract.pid})


class PeerReviewHandler(StatusHandler):
    def handle(self, article, request):
        logger.info("Setting status PEER_REVIEW pid=%s", article.abstract.pid)
        article.status = article.Status.PEER_REVIEW
        article.save()
        return Response({"status": "PEER_REVIEW set", "article pid": article.abstract.pid})
    
    
class PublishedHandler(StatusHandler):
    def handle(self, article, request):
        logger.info("Setting status PUBLISHED pid=%s", article.abstract.pid)
        # control on the DOI field mandatory
        if not article.doi:
            return Response(
                {"error": "DOI is mandatory if published"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # quick synchronous validation before scheduling
        article_data = article.data if isinstance(article.data, dict) else {}
        if not article_data.get("title"):
            return Response(
                {"error": "Article data title is mandatory if published"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # run save_citation synchronously; publish only on success
        try:
            save_citation(article_id=article.pk)
        except Exception as exc:
            logger.exception("save_citation failed pid=%s", article.abstract.pid)
            return Response(
                {"error": "save_citation failed", "details": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # set the publication_date to now
        article.publication_date = timezone.now()
        article.status = article.Status.PUBLISHED
        article.save()
        return Response({"status": "PUBLISHED set", "article pid": article.abstract.pid})


class RejectedHandler(StatusHandler):
    def handle(self, article, request):
        logger.info("Setting status REJECTED pid=%s", article.abstract.pid)
        article.status = article.Status.REJECTED
        article.save()
        return Response({"status": "REJECTED set", "article pid": article.abstract.pid})
    