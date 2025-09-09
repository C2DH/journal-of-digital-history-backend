import logging
from django.conf import settings
from jsonschema.exceptions import ValidationError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from jdhapi.utils.bluesky import launch_social_media_bluesky
from jdhapi.utils.facebook import launch_social_media_facebook

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def bluesky_campaign(request):
    """
    POST /api/articles/bluesky

    Endpoint to launch a social media campaign for an article on Bluesky.
    It schedules a social media post on Bluesky with a link to the article.
    Requires admin permissions.

    Request :
        repository_url: str : URL of the GitHub repository containing the article
        article_url: str : URL of the article to promote
        image_file: str (optional) : URL or path to the image file to include in the post
        scheduled_time: array str (optional) : Scheduled time for the post in ISO 8601
        scheduled_independent: array str (optional) : Scheduled time for independent posts in ISO 8601
    """

    logger.info("POST /api/articles/bluesky")

    try:
        logger.info("Bluesky campaign started.")
        bluesky_data = launching_bluesky_campaign(request)
        return Response(
            {
                "message": "Bluesky campaign launched successfully.",
                "data": bluesky_data,
            },
            status=status.HTTP_200_OK,
        )
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return Response(
            {"error": "ValueError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {e}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error("An unexpected error occurred.")
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def facebook_campaign(request):
    """
    POST /api/articles/facebook

    Endpoint to launch a social media campaign for an article on Facebook.
    It schedules a social media post on Facebook with a link to the article.
    Requires admin permissions.

    Request :
        repository_url: str : URL of the GitHub repository containing the article
        article_url: str : URL of the article to promote
        image_file: str (optional) : URL or path to the image file to include in the post
        scheduled_time: array str (optional) : Scheduled time for the post in ISO 8601
        scheduled_independent: array str (optional) : Scheduled time for independent posts in ISO 8601
    """

    logger.info("POST /api/articles/facebook")

    try:
        logger.info("Facebook campaign started.")
        facebook_data = launching_facebook_campaign(request)
        return Response(
            {
                "message": "Facebook campaign launched successfully.",
                "data": facebook_data,
            },
            status=status.HTTP_200_OK,
        )
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return Response(
            {"error": "ValueError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {e}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error("An unexpected error occurred.")
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )


def launching_bluesky_campaign(request):
    """
    Helper function to launch a Bluesky campaign.
    """
    logger.info("Launching Bluesky campaign...")

    repository_url = request.data.get("repository_url")
    article_url = request.data.get("article_url")
    schedule_main = request.data.get("schedule_main")

    data = launch_social_media_bluesky(
        repo_url=repository_url,
        branch="main",
        article_link=article_url,
        login=settings.BLUESKY_JDH_ACCOUNT,
        password=settings.BLUESKY_JDH_PASSWORD,
        schedule_main=schedule_main,
    )

    return data


def launching_facebook_campaign(request):
    """
    Helper function to launch a Facebook campaign.
    """
    logger.info("Launching Facebook campaign...")

    repository_url = request.data.get("repository_url")
    article_url = request.data.get("article_url")
    schedule_main = request.data.get("schedule_main")

    data = launch_social_media_facebook(
        repo_url=repository_url,
        branch="main",
        article_link=article_url,
        page_id=settings.FACEBOOK_JDH_PAGE_ID,
        access_token=settings.FACEBOOK_JDH_ACCESS_TOKEN,
        schedule_main=schedule_main,
    )

    return data
