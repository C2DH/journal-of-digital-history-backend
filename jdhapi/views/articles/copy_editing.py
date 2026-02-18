import io
import logging
import requests
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import EmailMessage
from jsonschema.exceptions import ValidationError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from jdhapi.models import Article
from jdhapi.utils.run_github_action import trigger_workflow_and_wait

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_docx(request):
    """
    Helper function to get the docx file path from the request.
    """
    branch_name = "pandoc"
    pid = request.GET.get("pid")
    
    if not pid:
        return Response({"error": "Article PID is required."}, status=400)
    try:
        workflow_error = ensure_pandoc_workflow(pid)
        if workflow_error:
            return workflow_error

        docx_bytes = fetch_docx_bytes(pid, branch_name)
        return HttpResponse(
            docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="article_{pid}.docx"'},
        )
    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=404)
    except ValueError as e:
        return Response({"error": str(e)}, status=502)
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to get article.docx", "details": str(e)}, status=500
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def send_docx_email(request):
    """
    Send the docx as an email attachment.
    """
    branch_name = "pandoc"
    pid = request.GET.get("pid")
    if not pid:
        return Response({"error": "Article PID is required."}, status=400)

    try:
        workflow_error = ensure_pandoc_workflow(pid)
        if workflow_error:
            return workflow_error

        docx_bytes = fetch_docx_bytes(pid, branch_name)
        send_email_copy_editor(pid, docx_bytes)
        return Response({"status": "sent", "pid": pid})
    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=404)
    except ValueError as e:
        return Response({"error": str(e)}, status=502)
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to get article.docx", "details": str(e)}, status=500
        )
    except Exception as e:
        return Response({"error": "Failed to send email", "details": str(e)}, status=502)


def fetch_docx_bytes(pid, branch_name):
    url = f"https://api.github.com/repos/jdh-observer/{pid}/contents/article.docx?ref={branch_name}"
    headers = {"Authorization": f"Bearer {settings.GITHUB_ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        download_url = data.get("download_url")

        if not download_url:
            raise ValueError("Download URL not available for the file.")

        file_response = requests.get(download_url)
        file_response.raise_for_status()
        return file_response.content
    if response.status_code == 404:
        raise FileNotFoundError(f"article.docx file not found for article ID '{pid}'.")

    raise ValueError("Unexpected error occurred while contacting GitHub API.")
    

def send_email_copy_editor(pid, docx_bytes):
    COPY_EDITOR_ADDRESS = "elisabeth.guerard@uni.lu"
    body = "Dear Andy, find in attachment the docx to review for copy-editing"
    filename = f"article_{pid}.docx"
    message = EmailMessage(
        subject="Article to review for copy-editing",
        body=body,
        from_email="jdh.admin@uni.lu",
        to=[COPY_EDITOR_ADDRESS],
    )
    message.attach(
        filename,
        docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    message.send(fail_silently=False)


def run_pandoc_workflow(repository_url):
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
        raise


def ensure_pandoc_workflow(pid):
    try:
        try:
            article = Article.objects.get(abstract__pid=pid)
        except Article.DoesNotExist:
            return Response(
                {"error": f"Article not found for PID '{pid}'."}, status=404
            )

        if not article.repository_url:
            return Response(
                {"error": f"repository_url is missing for PID '{pid}'."},
                status=400,
            )

        logger.debug(
            "Run pandoc workflow and wait for completion pid=%s, repo=%s",
            pid,
            article.repository_url,
        )
        run_pandoc_workflow(article.repository_url)
        logger.debug("Pandoc workflow completed for pid=%s", pid)
    except Exception as e:
        return Response(
            {"error": "Failed to run pandoc workflow", "details": str(e)},
            status=502,
        )

    return None