from jdh.validation import JSONSchema
from jdhapi.models import Article
from django.db import transaction
from jsonschema.exceptions import ValidationError, SchemaError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from ..logger import logger as get_logger

logger = get_logger()
article_status_schema = JSONSchema(filepath="article_status.json")


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def update_article_status(request):
    """
    PATCH /api/articles/status

    Endpoint to modify the status of an abstract identified by its PID.
    It sends an email notification to the contact email of the abstract.
    Requires admin permissions.
    """

    try:
        data = change_status(request)
        return Response(
            {"message": "Abstract updated successfully.", "data": data},
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {e}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except SchemaError as e:
        logger.exception("Schema error occurred.")
        return Response(
            {"error": "SchemaError", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )
    except (KeyError, IndexError) as e:
        logger.exception("Data invalid after validation")
        return Response(
            {"error": "KeyError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
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


def change_status(request):
    """
    Change article(s) status(es) with no notification.
    Args:
        request: containing email data (from, to, subject, message).
        pids: PID(s) of the abstract(s) to be modified.
    """
    logger.info("Change article status")
    logger.info("Start JSON validation")
    with transaction.atomic():

        article_status_schema.validate(instance=request.data)

        pids = request.data.get("pids", [])
        status = request.data.get("status", "").upper()

        try:
            logger.info("Retrieve article(s) according to PID(s).")
            if not pids:
                logger.error("No PID provided in request data.")
                raise ValidationError({"error": "At least one PID is required."})
            articles = Article.objects.filter(abstract__pid__in=pids)

            if not articles.exists():
                logger.error(f"No article(s) found for PID(s) : {pids}.")
                raise Exception({"error": "Article(s) not found."})

        except Article.DoesNotExist:
            logger.error(f"Article(s) with PID(s) {pids} do not exist.")
            raise Exception({"error": "Article(s) not found."})

        updated_articles = []

        for article in articles:
            article.status = status
            article.save()

            updated_articles.append(
                {
                    "pid": article.abstract.pid,
                    "data": article.data,
                    "new_status": article.status,
                }
            )
            logger.info(
                f"Article {article.abstract.pid} status updated to {article.status}."
            )

    return updated_articles
