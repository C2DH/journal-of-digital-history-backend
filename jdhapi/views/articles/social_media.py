import base64
import io
import logging
import requests
from PIL import Image
from django.conf import settings
from jsonschema.exceptions import ValidationError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from jdhapi.utils.bluesky import launch_social_media_bluesky, fetch_image, fetch_link_metadata
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


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_tweet_md_file(request):
    """
    Helper function to get the tweet markdown file path from the request.
    """
    pid = request.GET.get("pid")
    if not pid:
        raise ValueError("Article PID is required.")

    url = f"https://api.github.com/repos/jdh-observer/{pid}/contents/tweets.md"
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_ACCESS_TOKEN}"  
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            content = response.json()["content"]
            decoded_tweet = base64.b64decode(content).decode("utf-8")

            return Response({"content": decoded_tweet}, status=200)
        elif response.status_code == 404:
            raise ValueError(f"Tweet.md file not found for article ID '{pid}'.")
        else:
            raise ValueError("Unexpected error occurred while contacting GitHub API.")

    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to get Tweet.md", "details": str(e)}, status=500
        )
    
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_social_cover_image(request):
    """
    Helper function to get the social media cover image path from the request.
    """
    pid = request.GET.get("pid")
    if not pid:
        raise ValueError("Article PID is required.")

    url = f"https://api.github.com/repos/jdh-observer/{pid}/contents/socialmediacover.png?ref=main"
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_ACCESS_TOKEN}"  
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return Response({"download_url": response.json()["download_url"]}, status=200)
        elif response.status_code == 404:
            raise ValueError(f"socialmediacover.png file not found for article ID '{pid}'.")
        else:
            raise ValueError("Unexpected error occurred while contacting GitHub API.")


    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to get socialmediacover.png", "details": str(e)}, status=500
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
