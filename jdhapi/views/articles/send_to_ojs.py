import marko 
import requests
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from jdhapi.models import Article
from jdh.validation import JSONSchema
from jdhseo.utils import get_country_with_ROR
from jsonschema.exceptions import ValidationError
from lxml import html
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from weasyprint import HTML

from ..logger import logger as get_logger

logger = get_logger()
article_to_ojs_schema = JSONSchema(filepath="article_to_ojs.json")
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {settings.OJS_API_KEY_TOKEN}'
}
OJS_API_URL = settings.OJS_API_URL

@api_view(["POST"])
@permission_classes([IsAdminUser])
def send_article_to_ojs(request):
    """
    POST /api/articles/ojs 

    Endpoint to send an article ready for peer review to OJS.
    Requires admin permissions.
    """

    logger.info("POST /api/articles/ojs")

    try:
        res = submit_to_ojs(request)
        return Response(
            {"message": "Article(s) send successfully to OJS.", "data": res},
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {str(e)}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except (KeyError, IndexError) as e:
        logger.exception(f"Data invalid after validation: {str(e)}")
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
            raise ValidationError( "One article PID is required.")
        
        article = Article.objects.get(abstract__pid=pid)

        if article is None:
            logger.error(f"No article found for PID : {pid}.")
            raise Exception( "Article not found.")
    
        logger.info("Send article to OJS.")

        submission_id = 0
        publication_id = 0
        contributor_id = 0

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
                    author_name=f"{author.firstname} {author.lastname}" 
                    error_msg = f"Author {fieldname} is missing. Author concerned : {author_name}"
                    logger.error(error_msg)
                    if fieldname == 'country' : 
                        country = get_country_with_ROR(affiliation_name=author.affiliation)
                        if not country:
                            raise ValidationError(error_msg)
                        else:
                            author.country = country
                            author.save()
                            return
                        
                    raise ValidationError(error_msg)

        try:
            # 1. create a blank submission in OJS
            res = create_blank_submission()
            logger.info(f"Blank submission created with response: {res.json()}")

            submission_id = res.json().get('id',0)
            publication_id = res.json().get('currentPublicationId', 0)
             
            # 2. upload the pdf file to OJS
            pdf_file = generate_pdf_for_submission(article)
            res = upload_manuscript_to_ojs(article.abstract.pid, submission_id, pdf_file)

            if res.status_code not in [200, 201]:
                error_msg = f"Failed to upload manuscript to OJS. Status: {res.status_code}, Response: {res.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Manuscript uploaded with response: {res.json()}")

            # 3. Create the article contributor in OJS
            primary_contact_id=create_contributor_in_ojs(submission_id, publication_id, article)
            
            if not primary_contact_id:
                raise Exception("Failed to create contributor or retrieve primary contact ID")

            contributor_id=primary_contact_id

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


def create_blank_submission(): 
    logger.info("creating a blank submission in OJS")

    url = f"{OJS_API_URL}/submissions"
    payload= {
        "commentsForTheEditors": "none",
        "locale":"en",
        "sectionId":1
    }
    res = requests.post(url=url, headers=headers, json=payload )

    return res

def upload_manuscript_to_ojs(pid, submission_id, pdf_bytes):
    logger.info("uploading manuscript to OJS")

    url=f"{OJS_API_URL}/submissions/{submission_id}/files"
    headers_form_data = {
        'Authorization': f'Bearer {settings.OJS_API_KEY_TOKEN}'
    }
    files = {
        "file": (f"peer_review_{pid}.pdf", pdf_bytes, "application/pdf"),
    }
    data={
        "fileStage": 2, # 2 is for stage SUBMISSION_FILE_SUBMISSION
        "genreId": 1, # 1 is for manuscript
    }

    res=requests.post(url=url, headers=headers_form_data, files=files, data=data)

    return res

def create_contributor_in_ojs(submission_id, publication_id, article: Article): 
    logger.info("creating the article contributor in OJS")  

    primary_contact_id = 0 

    url=f"{settings.OJS_API_URL}/submissions/{submission_id}/publications/{publication_id}/contributors"

    for author in article.abstract.authors.all():
        logger.info(f"Contributor {author.firstname} {author.lastname} creation in OJS")
        payload = {
            "affiliation": {
                "en": author.affiliation
            },
            "country": str(author.country),
            "email":  author.email,
            "familyName": {
                "en":  author.lastname
            },
            "fullName": f"{author.firstname} {author.lastname}",
            "givenName": {
                "en": author.firstname
            },
            "includeInBrowse": True,
            "locale": "en",
            "orcid": author.orcid,
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
        res = requests.post(url=url, headers=headers, json=payload)
        logger.info(f"Contributor {author.firstname} {author.lastname} created with response: {res.json()}")

        if article.abstract.contact_email == author.email and article.abstract.contact_lastname == author.lastname :
            primary_contact_id = res.json().get('id',0) 

    return primary_contact_id

def assign_primary_contact_and_metadata(submission_id, publication_id, contributor_id, article):
    logger.info("Assign the author as primary contact to the submission and add title, abstract and competingInterests")

    url=f"{OJS_API_URL}/submissions/{submission_id}/publications/{publication_id}"
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

    res=requests.put(url=url, headers=headers, json=payload)

    return res

def submit_submission_to_ojs(submission_id):
    logger.info("Submit the article to OJS")

    url=f"{OJS_API_URL}/submissions/{submission_id}/submit"
    payload= {
        "confirmCopyright": "true"
    }

    res=requests.put(url, headers=headers, json=payload)

    return res

def generate_pdf_for_submission(article):
    template = "jdhseo/peer_review.html"
    if "title" in article.data:
        articleTitle = html.fromstring(
            marko.convert(article.abstract.title)
        ).text_content()
        context = {"article": article, "articleTitle": articleTitle}
        html_string = render_to_string(template, context)

        # Generate the PDF
        pdf_file = HTML(string=html_string).write_pdf()

        logger.info("Pdf generated")
        return pdf_file
    
