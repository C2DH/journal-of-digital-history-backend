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
        file_id = 0
        contributor_id = 0

        # Here in the middle we need to write the different steps which are : 

       
        # 3. Create the article contributor in OJS
        # 4. Assign the author as primary Contact to the submission + title + abstract + competingInterests 
        # 5. Submit the submission to OJS

        # 1. create a blank submission in OJS
        res = create_blank_submission()

        submission_id = res.json().get('id',0)
        publication_id = res.json().get('currentPublicationId', 0)
        
         # 2. upload the pdf file to OJS

        res = upload_manuscript_to_ojs(submission_id, "TO_DO_TO_MODIFY_HERE" )

        file_id = res.json().get('fileId',0)

        

        article.status = 'PEER_REVIEW'
        article.save()


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
    url=f"{OJS_API_URL}/submission/{submission_id}/files"
    payload={
        "file": open(file_path, 'rb'),
        "fileStage": 1, # 1 is for stage SUBMISSION_FILE_SUBMISSION
        "genreId": 1, # 1 is for manuscript
    }

    res=requests.post(url=url, authentication=bearer_token, headers=headers, files=payload)

    return res
