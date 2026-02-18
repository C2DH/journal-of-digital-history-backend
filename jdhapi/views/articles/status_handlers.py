import logging
from rest_framework.response import Response
from jdhapi.models import Article
from jdhapi.views.articles.copy_editing import send_docx_email_pid

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
        email_response = send_docx_email_pid(article.abstract.pid)
        if getattr(email_response, "status_code", 200) >= 400:
            logger.warning(
                "COPY_EDITING email failed pid=%s status_code=%s",
                article.abstract.pid,
                getattr(email_response, "status_code", None),
            )
            return email_response

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
    