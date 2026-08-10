from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from jdhapi.models import Author
from jdhapi.utils.logger import logger as get_logger

logger = get_logger()


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_authors_returning(request):
    """
    GET /api/authors/stats

    Endpoint to get the statistics "first time authors" vs "returning authors".
    """

    try:
        data = stats_author_returning()
        return Response(
            {
                "message": "Statistics for first-time vs returning author received.",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )


def stats_author_returning():

    qs = Author.objects.annotate(total_abstracts=Count("abstracts", distinct=True))
    #  abstracts is a related name for authors field in Abstract model
    first_time = qs.filter(total_abstracts__lte=1).count()
    returning = qs.filter(total_abstracts__gte=2).count()

    return [
        {"id": 0, "value": first_time, "label": "First time authors"},
        {"id": 1, "value": returning, "label": "Returning authors"},
    ]
