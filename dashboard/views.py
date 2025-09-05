import logging
import re
import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from jdhapi.models import Abstract
from jsonschema.exceptions import ValidationError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from dashboard import socialmedia


logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def bluesky_campaign(request):
    """
    POST /dashboard/promotion/bluesky

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

    logger.info("POST /dashboard/promotion/bluesky")

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
    POST /dashboard/promotion/facebook

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

    logger.info("POST /dashboard/promotion/facebook")

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
    image_file = request.data.get("image_file")
    schedule_main = request.data.get("schedule_main")
    schedule_independent = request.data.get("schedule_independent")

    data = socialmedia.launch_social_media_bluesky(
        repo_url=repository_url,
        image_file=image_file,
        branch="main",
        article_link=article_url,
        login=settings.BLUESKY_JDH_ACCOUNT,
        password=settings.BLUESKY_JDH_PASSWORD,
        schedule_main=schedule_main,
        schedule_independent=schedule_independent,
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

    data = socialmedia.launch_social_media_facebook(
        repo_url=repository_url,
        branch="main",
        article_link=article_url,
        page_id=settings.FACEBOOK_JDH_PAGE_ID,
        access_token=settings.FACEBOOK_JDH_ACCESS_TOKEN,
        schedule_main=schedule_main,
    )

    return data


@staff_member_required
def fingerprint(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    article = abstractsubmission.article
    # url of type
    RAW_GIT = "https://raw.githubusercontent.com"
    GIT_USER = "jdh-observer"
    gitRepo = article.issue.pid + "-" + article.abstract.pid
    notebookPath = article.notebook_path
    rawUrl = RAW_GIT + "/" + GIT_USER + "/" + gitRepo + "/main/" + notebookPath
    try:
        generateStat(article, rawUrl)(article, rawUrl)
    except Exception as e:
        print(rawUrl)
        print(e)
    # redirect to a new URL:
    return render(
        request,
        "dashboard/abstract_detail.html",
        {"abstractsubmission": abstractsubmission, "article": article},
    )


def generateStat(article, rawUrl):
    r = requests.get(rawUrl)
    notebook = r.json()
    # use the cached response
    cells = notebook.get("cells")
    # output
    cells_stats = []
    for cell in cells:
        c = {"type": cell["cell_type"]}
        # just skip if it's empty
        source = cell.get("source", [])
        if not source:
            continue
            # check cell metadata
        tags = cell.get("metadata").get("tags", [])
        if "hidden" in tags:
            continue
        c["countLines"] = len(source)
        c["countChars"] = len("".join(source))
        c["tags"] = tags
        # c['source'] = cell.get('source')
        c["isMetadata"] = any(
            tag in ["title", "abstract", "contributor", "disclaimer"] for tag in tags
        )
        c["isHermeneutic"] = any(
            tag in ["hermeneutics", "hermeneutics-step"] for tag in tags
        )
        c["isFigure"] = any(tag.startswith("figure-") for tag in tags)
        c["isFullWidth"] = any(tag == "full-width" for tag in tags)
        c["isHeading"] = (
            cell["cell_type"] == "markdown"
            and re.match(r"\s*#+\s", "".join(cell.get("source"))) is not None
        )
        cells_stats.append(c)

    general_stats = {
        "countLines": sum([c["countLines"] for c in cells_stats]),
        "countChars": sum([c["countChars"] for c in cells_stats]),
        "countContributors": sum(
            ["contributor" in c["tags"] for c in cells_stats],
        ),
        "countHeadings": sum([c["isHeading"] for c in cells_stats]),
        "countHermeneuticCells": sum(
            [c["isHermeneutic"] for c in cells_stats],
        ),
        "countHermeneuticOnlyCells": sum(
            ["hermeneutics" in c["tags"] for c in cells_stats]
        ),
        "countCodeCells": sum([c["type"] == "code" for c in cells_stats]),
        "countCells": len(cells_stats),
        "extentChars": [
            min([c["countChars"] for c in cells_stats]),
            max([c["countChars"] for c in cells_stats]),
        ],
        "extentLines": [
            min([c["countLines"] for c in cells_stats]),
            max([c["countLines"] for c in cells_stats]),
        ],
    }
    article.data = {"stats": general_stats, "cells": cells_stats}
    article.save()
