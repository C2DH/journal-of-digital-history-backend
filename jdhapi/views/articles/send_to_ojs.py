import requests
from django.db import transaction
from jdhapi.models import Article
from jdh.validation import JSONSchema
from jsonschema.exceptions import ValidationError
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from settings import OJS_API_KEY_TOKEN as bearer_token, OJS_API_URL

from ..logger import logger as get_logger

logger = get_logger()
article_to_ojs_schema = JSONSchema(filepath="article_to_ojs.json")
headers='application/json'

@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_article_to_ojs(request):
    """
    POST /api/articles/ojs 

    Endpoint to send an article ready for peer review to OJS.
    Requires admin permissions.
    """

    try:
        res = submit_to_ojs(request)
        return Response(
            {"message": "Article(s) send successfully to OJS.", "data": res},
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {e}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
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
    


def submit_to_ojs(request):

    logger.info('Submitting article to OJS')

    with transaction.atomic():

        article_to_ojs_schema.validate(instance=request.data)

        pid = request.data.get("pid", None)

        logger.info("Retrieve article according to the PID.")

        if not pid: 
            logger.error("No PID provided in request data.")
            raise ValidationError({"error": "One article PID is required."})
        
        article = Article.objects.filter(abstract__pid__in=pid)

        if not article.exists():
            logger.error(f"No article found for PID : {pid}.")
            raise Exception({"error": "Article not found."})
    
        logger.info("Send article to OJS.")

        submission_id = 0
        publication_id = 0
        contributor_id = 0

        try:
            # 1. create a blank submission in OJS
            res = create_blank_submission()

            submission_id = res.json().get('id',0)
            publication_id = res.json().get('currentPublicationId', 0)
            
            # 2. upload the pdf file to OJS
            res = upload_manuscript_to_ojs(submission_id, "TO_DO_TO_MODIFY_HERE")

            # 3. Create the article contributor in OJS
            res=create_contributor_in_ojs(submission_id, publication_id, article)

            contributor_id=res.json().get('contributor_id',0)

            # 4. Assign the author as primary Contact to the submission + title + abstract + competingInterests 
            assign_primary_contact_and_metadata(submission_id, publication_id, contributor_id, article)

            # 5. Submit the submission to OJS

            # TOD_DO uncomment once everything else is checked
            # submit_to_ojs(submission_id)
        except Exception as e:
            logger.error(f"Error during OJS submission process: {e}")
            raise e

        try:
            logger.info("Update article status to PEER_REVIEW")
            article.status = 'PEER_REVIEW'
            article.save()
        except Exception as e:
            logger.error(f"Failed to update article status: {e}")
            raise e


def create_blank_submission(): 
    logger.info("creating a blank submission in OJS")

    url = f"{OJS_API_URL}/submissions"
    payload= {
        "commentsForTheEditors": "none",
        "locale":"en",
        "sectionId":1
    }
    res = requests.post(url=url, authentication=bearer_token, headers=headers, json=payload )

    return res

def upload_manuscript_to_ojs(submission_id, file_path):
    logger.info("creating a blank submission in OJS")

    url=f"{OJS_API_URL}/submission/{submission_id}/files"
    payload={
        "file": open(file_path, 'rb'),
        "fileStage": 1, # 1 is for stage SUBMISSION_FILE_SUBMISSION
        "genreId": 1, # 1 is for manuscript
    }

    res=requests.post(url=url, authentication=bearer_token, headers=headers, files=payload)

    return res

def create_contributor_in_ojs(submission_id, publication_id, article): 
    logger.info("creating the article contributor in OJS")  

    url=f"{OJS_API_URL}/submission/{submission_id}/publications/{publication_id}/contributors"
    payload = {
        "affiliation": {
            "en": article.authors.first().affiliation
        },
        "country": "TO_DO_TO_IMPLEMENT_COUNTRY_CODE",
        "email":  article.authors.first().email,
        "familyName": {
            "en":  article.authors.first().last_name
        },
        "fullName": f"{article.authors.first().first_name} {article.authors.first().last_name}",
        "givenName": {
            "en": article.authors.first().first_name
        },
        "includeInBrowse": True,
        "locale": "en",
        "orcid": article.authors.first().orcid,
        "preferredPublicName": {
            "en": ""
        },
        "publicationId": publication_id,
        "seq": 0,
        "userGroupId": 14,
        "userGroupName": {
            "en": "Author"
        }
    }

    res = requests.post(url=url, authentication=bearer_token, headers=headers, json=payload)

    return res

def assign_primary_contact_and_metadata(submission_id, publication_id, contributor_id, article):
    logger.info("Assign the author as primary contact to the submission and add title, abstract and competingInterests")

    url=f"{OJS_API_URL}/submission/{submission_id}/publications/{publication_id}"
    payload={
        "primaryContactId": contributor_id,
        "title": {
            "en": article.abstract.title
        },
        "abstract": {
            "en": article.abstract.abstract
        },
        "competingInterests": {
            "en":  "I declare that I have no competing interests"
        }
    }

    res=requests.put(url=url, authentication=bearer_token, headers=headers, json=payload)

    return res

def submit_submission_to_ojs(submission_id):
    logger.info("Submit the article to OJS")

    url=f"{OJS_API_URL}/submissions/{submission_id}/submit"
    payload= {
        "confirmCopyright": "true"
    }

    res=requests.put(url, authentication=bearer_token, headers=headers, json=payload)

    return res

