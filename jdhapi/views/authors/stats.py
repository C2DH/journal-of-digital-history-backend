from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from jdhapi.models import Abstract, Author
from jdhapi.utils.logger import logger as get_logger

logger = get_logger()


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_authors_stats(request):
    """
    GET /api/authors/stats

    Endpoint to get the statistics "first time authors" vs "returning authors".
    """

    try:
        returning = stats_author_returning()
        coauthorship = stats_co_authorship()
        return Response(
            {
                "message": "Statistics for author dashboard page.",
                "first-time_vs_returning": returning,
                "coauthorship": coauthorship
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
    """
    First-time author vs returning author data :
    'first-time' author have only submitted one abstract where 'returning' have submitted more than 1.
    """

    qs = Author.objects.annotate(total_abstracts=Count("abstracts", distinct=True))
    #  abstracts is a related name for authors field in Abstract model
    first_time = qs.filter(total_abstracts__lte=1).count()
    returning = qs.filter(total_abstracts__gte=2).count()

    return [
        {"id": 0, "value": first_time, "label": "First time authors"},
        {"id": 1, "value": returning, "label": "Returning authors"},
    ]


def stats_co_authorship():
    """
    Classification of the authors regarded with how many co-authors they have worked.
    '1 author' : author has been working alone on their article
    '2 authors' : author has been working with another author on their article
    '3 authors' : author has been working with three authors on their article
    '4 authors' : author has been working with 4 authors or even more on their article
    """

    qs = Abstract.objects.annotate(total_authors=Count("authors", distinct=True))
    one_author = qs.filter(total_authors=1).count()
    two_authors = qs.filter(total_authors=2).count()
    three_authors = qs.filter(total_authors=3).count()
    many_authors = qs.filter(total_authors__gte=4).count()

    return [
        {"id": 0, "value": one_author, "label": "1 author"},
        {"id": 1, "value": two_authors, "label": "2 authors"},
        {"id": 2, "value": three_authors, "label": "3 authors"},
        {"id": 3, "value": many_authors, "label": "4+ authors"},
    ]
