import logging

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from jdhapi.models import Article
from jdhapi.utils.github_action import trigger_workflow_and_wait

logger = logging.getLogger(__name__)

COPY_EDITOR_ADDRESS = settings.COPY_EDITOR_ADDRESS


class DocxWorkflowError(Exception):
    """Base class for all docx/email pipeline failures (carries a client-safe message)."""


class PandocWorkflowError(DocxWorkflowError):
    """The GitHub Actions pandoc workflow failed, was interrupted, or timed out."""


class ArticleFetchError(DocxWorkflowError):
    """article.docx could not be retrieved from GitHub after the workflow ran."""


class EmailDeliveryError(DocxWorkflowError):
    """The docx was generated/fetched successfully but could not be emailed."""


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_docx(request):
    """
    GET api/articles/docx

    Helper function to get the docx file from the request.
    Needs a pid in the request query parameters.
    """
    branch_name = "pandoc"
    pid = request.GET.get("pid")

    if not pid:
        return Response({"error": "Article PID is required."}, status=400)

    logger.info("GET api/articles/docx pid=%s", pid)

    try:
        ensure_pandoc_workflow(pid)
        docx_bytes = fetch_docx_bytes(pid, branch_name)
        return HttpResponse(
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="article_{pid}.docx"'},
            status=200
        )
    except FileNotFoundError as e:
        logger.warning("pid=%s not found: %s", pid, e)
        return Response({"error": str(e)}, status=404)
    except ValueError as e:
        logger.warning("pid=%s bad request: %s", pid, e)
        return Response({"error": str(e)}, status=400)
    except PandocWorkflowError as e:
        logger.exception("pid=%s pandoc workflow failed: %s", pid, e, exc_info=True)
        return Response({"error": "Failed to generate docx via pandoc workflow.", "details": str(e)}, status=502)
    except ArticleFetchError as e:
        logger.exception("pid=%s docx fetch failed: %s", pid, e, exc_info=True)
        return Response({"error": "Failed to retrieve generated docx from GitHub.", "details": str(e)}, status=502)
    except Exception as e:
        logger.exception("pid=%s unexpected error in get_docx", pid)
        return Response({"error": "Unexpected server error.", "details": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_docx_email(request):
    """
    POST api/articles/docx/email

    Send the docx as an email attachment.
    :params pid: the article PID
    :params body: the email body to send to copy editor
    :params branch_name: the branch name where the docx file is located, by default "pandoc"
    """
    branch_name = "pandoc"
    pid = request.data.get("pid")
    subject = request.data.get("subject", "Article to review for copy editing")
    body = request.data.get("body")

    if not pid:
        return Response({"error": "Article PID is required."}, status=400)

    logger.info("POST api/articles/docx/email pid=%s", pid)

    try:
        ensure_pandoc_workflow(pid)
        docx_bytes = fetch_docx_bytes(pid, branch_name)
        send_email_copy_editor(pid, subject, docx_bytes, body)
    except FileNotFoundError as e:
        logger.warning("pid=%s not found: %s", pid, e)
        return Response({"error": str(e)}, status=404)
    except ValueError as e:
        logger.warning("pid=%s bad request: %s", pid, e)
        return Response({"error": str(e)}, status=400)
    except PandocWorkflowError as e:
        logger.exception("pid=%s pandoc workflow failed: %s", pid, e, exc_info=True)
        return Response({"error": "Failed to generate docx via pandoc workflow.", "details": str(e)}, status=502)
    except ArticleFetchError as e:
        logger.exception("pid=%s docx fetch failed: %s", pid, e, exc_info=True)
        return Response({"error": "Failed to retrieve generated docx from GitHub.", "details": str(e)}, status=502)
    except EmailDeliveryError as e:
        logger.exception("pid=%s email delivery failed: %s", pid, e, exc_info=True)
        return Response({"error": "Docx generated but email delivery failed.", "details": str(e)}, status=502)
    except Exception as e:
        logger.exception("pid=%s unexpected error in send_docx_email", pid)
        return Response({"error": "Unexpected server error.", "details": str(e)}, status=500)

    return Response({"message": f"Docx sent successfully by email for article : {pid}"}, status=200)


def fetch_docx_bytes(pid, branch_name):
    """
    Helper function to fetch the docx
    :params pid: the article PID
    :params branch_name: the branch name where the docx file is located
    """
    logger.info("[fetch_docx_bytes] Fetch the docx document for the article with PID '%s'", pid)

    url = f"https://api.github.com/repos/jdh-observer/{pid}/contents/article.docx?ref={branch_name}"
    headers = {"Authorization": f"Bearer {settings.GITHUB_ACCESS_TOKEN}"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException as e:
        raise ArticleFetchError(f"Network error contacting GitHub for article '{pid}': {e}") from e

    if response.status_code == 404:
        raise FileNotFoundError(f"article.docx file not found for article ID '{pid}'.")

    if response.status_code != 200:
        raise ArticleFetchError(
            f"GitHub returned {response.status_code} while fetching article.docx for '{pid}'."
        )

    download_url = response.json().get("download_url")
    if not download_url:
        raise ArticleFetchError(f"Download URL not available for article.docx (pid='{pid}').")

    try:
        file_response = requests.get(download_url, timeout=15)
        file_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ArticleFetchError(f"Failed to download article.docx for '{pid}': {e}") from e

    return file_response.content


def send_email_copy_editor(pid, subject, docx_bytes, body):
    """
    Helper function to send the email to copy editing editor
    :params pid: the article PID
    :params docx_bytes: the content of the docx file in bytes
    """
    logger.info("[send_email_copy_editor] Send email to copy editor for article '%s'", pid)

    filename = f"article_{pid}.docx"
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[COPY_EDITOR_ADDRESS, settings.DEFAULT_TO_EMAIL],
    )
    message.attach(
        filename,
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    try:
        message.send(fail_silently=False)
    except Exception as e:
        raise EmailDeliveryError(f"Failed to email docx for '{pid}': {e}") from e


def run_pandoc_workflow(repository_url):
    """
    Helper function to run the pandoc workflow will be executed
    :params repository_url: the article GitHub repository URL
    """
    logger.info("[run_pandoc_workflow] Running pandoc workflow for this repository: '%s'", repository_url)

    try:
        logger.debug(
            "run_pandoc_workflow wait repo=%s",
            repository_url,
        )
        trigger_workflow_and_wait(
            repository_url,
            workflow_filename="pandoc.yml",
        )
        logger.debug("Pandoc workflow completed repo=%s", repository_url)
    except Exception as e:
        logger.error("run_pandoc_workflow failed: %s", e)
        raise PandocWorkflowError(f"Failed to run pandoc workflow for '{repository_url}': {e}") from e


def ensure_pandoc_workflow(pid):
    """
    Helper function to ensure the pandoc workflow will be executed
    :params pid: the article PID
    """
    logger.info("[ensure_pandoc_workflow] Starting pandoc workflow for article with PID : '%s'", pid)

    try:
        article = Article.objects.get(abstract__pid=pid)
    except Article.DoesNotExist:
        raise FileNotFoundError(f"Article not found for article '{pid}'.")

    if not article.repository_url:
        raise ValueError(f"'repository_url' field is missing for article '{pid}'.")
    if not article.data:
        raise ValueError(f"'data' field is missing for article '{pid}'.")

    logger.debug(
        "Run pandoc workflow and wait for completion pid=%s, repo=%s",
        pid,
        article.repository_url,
    )
    run_pandoc_workflow(article.repository_url)
    logger.debug("Pandoc workflow completed for pid=%s", pid)