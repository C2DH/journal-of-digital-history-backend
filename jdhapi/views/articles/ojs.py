import requests
from django.conf import settings
from django.db import transaction
from jdh.validation import JSONSchema
from jdhseo.utils import get_country_with_ROR
from jsonschema.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from jdhapi.models import Article
from jdhapi.utils.logger import logger as get_logger
from jdhapi.utils.ojs import (
    assign_primary_contact_and_metadata,
    create_blank_submission,
    create_contributor_in_ojs,
    generate_pdf_for_submission,
    get_active_submission_with_timing,
    get_active_submissions_by_stage,
    get_active_submissions_with_decision,
    upload_manuscript_to_ojs,
)

logger = get_logger()
article_to_ojs_schema = JSONSchema(filepath="article_to_ojs.json")
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {settings.OJS_API_KEY_TOKEN}'
}
OJS_API_URL = settings.OJS_API_URL
OJS_WEBSITE_URL = settings.OJS_WEBSITE_URL


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_peer_review_article_with_decision(_):
    """
    GET /api/articles/ojs/submissions/decisions

    Get the list of all articles in peer review with the decisions from OJS.
    Requires admin permissions.
    """
    logger.info("GET /api/articles/ojs/submissions/decision")

    try:
        submissions_with_decisions = get_active_submissions_with_decision()
        return Response(
            {"data": submissions_with_decisions},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
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
def get_peer_review_article_with_timing(_):
    """
    GET /api/articles/ojs/submissions/decisions/timing

    Get the list of all articles in peer review with the timing (on-time, overdue) according to their round (R1, R1, R3+) from OJS.
    Requires admin permissions.
    """
    logger.info("GET /api/articles/ojs/submissions/decisions/timing")

    try:
        submissions_with_decisions = get_active_submission_with_timing()
        return Response(
            {"data": submissions_with_decisions},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
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
def get_peer_review_article_by_stage(_):
    """
    GET /api/articles/ojs/submissions/decisions/stage

    Get the list of all articles counts in peer review by stage(see below) according to their round (R1, R1, R3+) from OJS.
    Stages : 
    - Assign reviewer (assign)
    - Awaiting reviewer response (awaiting)
    - Review in progress (review)
    - Reviewer decision (reviewer)
    - Author revising (revising)
    Requires admin permissions.
    """
    logger.info("GET /api/articles/ojs/submissions/decisions/stage")

    try:
        submissions_with_decisions = get_active_submissions_by_stage()
        return Response(
            {"data": submissions_with_decisions},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
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
def get_count_submission_from_ojs(_):
    """
    GET /api/articles/ojs/submissions

    Get the list of all abstracts submitted to OJS ans being either in 'Incomplete' submission stage or 'Submission' 
    stage.
    Requires admin permissions.
    """

    logger.info("GET /api/articles/ojs/submissions")

    url = f"{OJS_API_URL}/submissions?stageIds=1"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return Response({"count": response.json().get("itemsMax", 0)}, status=200)
        else:
            return Response(
                {
                    "error": "Unexpected error occurred while contacting OJS API.",
                    "status_code": response.status_code,
                },
                status=response.status_code,
            )
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to connect to OJS API.", "details": str(e)}, status=500
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_article_to_ojs(request):
    """
    POST /api/articles/ojs/submission

    Endpoint to create an article submission ready for peer review to OJS.
    Requires admin permissions.
    """

    logger.info("POST /api/articles/ojs/submission")

    try:
        res = submit_to_ojs(request)
        return Response(
            {"message": "Article send successfully to OJS.", "data": res},
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {str(e)}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        ) 


def submit_to_ojs(request):

    logger.info('Submitting article to OJS')

    try:

        with transaction.atomic():

            article_to_ojs_schema.validate(instance=request.data)

            pid = request.data.get("pid", None)

            logger.info("Retrieve article according to the PID.")

            if not pid:
                logger.error("No PID provided in request data.")
                raise ValidationError("One article PID is required.")
            
            article = Article.objects.get(abstract__pid=pid)

            if article is None:
                logger.error(f"No article found for PID : {pid}.")
                raise Exception("Article not found.")
        
            logger.info("Send article to OJS.")

            submission_id = 0
            publication_id = 0
            contributor_id = 0
            is_one_contributor_primary_contact = False

            required_fields = {
                'affiliation': 'affiliation',
                'country': 'country',
                'email': 'email',
                'lastname': 'lastname',
                'firstname': 'firstname',
                'orcid': 'orcid',
            }

            for author in article.abstract.authors.all():
                for field, fieldname in required_fields.items():
                    if not getattr(author, field):
                        author_name = f"{author.firstname} {author.lastname}" 
                        error_msg = f"Author {fieldname} is missing. Author concerned : {author_name}"
                        logger.error(error_msg)
                        if fieldname == 'country': 
                            country = get_country_with_ROR(affiliation_name=author.affiliation)
                            if not country:
                                raise ValidationError(error_msg)
                            else:
                                author.country = country
                                author.save()
            
            for author in article.abstract.authors.all():
                if article.abstract.contact_email == author.email:
                    is_one_contributor_primary_contact = True
                    break
            
            if not is_one_contributor_primary_contact:
                error_msg = "No primary contact identified among authors."
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            if not article.data.get('title'):
                error_msg = "Field 'title' is missing in the 'data' field of the article."
                logger.error(error_msg)
                raise ValidationError(error_msg)

            try:
                # 1. create a blank submission in OJS
                res = create_blank_submission()
                logger.info(f"Blank submission created with response: {res.json()}")

                submission_id = res.json().get('id', 0)
                publication_id = res.json().get('currentPublicationId', 0)

                article.ojs_submission_id = submission_id
                article.save()
                
                # 2. upload the pdf file to OJS
                pdf_file = generate_pdf_for_submission(article)
                res = upload_manuscript_to_ojs(article.abstract.pid, submission_id, pdf_file)

                if res.status_code not in [200, 201]:
                    error_msg = f"Failed to upload manuscript to OJS. Status: {res.status_code}, Response: {res.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                logger.info(f"Manuscript uploaded with response: {res.json()}")

                # 3. Create the article contributor in OJS
                primary_contact_id = create_contributor_in_ojs(submission_id, publication_id, article)
                
                if not primary_contact_id:
                    raise Exception("Failed to create contributor or retrieve primary contact ID")

                contributor_id = primary_contact_id

                # 4. Assign the author as primary Contact to the submission + title + abstract + competingInterests 
                res = assign_primary_contact_and_metadata(submission_id, publication_id, contributor_id, article)

                if res.status_code not in [200, 201]:
                    error_msg = f"Failed to assign metadata. Status: {res.status_code}, Response: {res.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                # 5. Submit the submission to OJS
                # uncomment if we do not need human check on OJS dashboard anymore
                # submit_to_ojs(submission_id)

            except Exception as e:
                logger.error(f"Error during OJS submission process: {e}")
                raise e
            
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        raise e
