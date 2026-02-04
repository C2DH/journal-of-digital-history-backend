from rest_framework.response import Response
from jdhapi.models import Article

class StatusHandler:
    def handle(self, article, request):
        raise NotImplementedError

class TechnicalReviewHandler(StatusHandler):
    def handle(self, article, request):
        article.status = article.Status.TECHNICAL_REVIEW
        article.save()
        return Response({"status": "TECHNICAL_REVIEW set", "article pid": article.abstract.pid})

