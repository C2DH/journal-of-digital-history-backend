import marko
import requests
from django.conf import settings
from django.template.loader import render_to_string
from jdh.validation import JSONSchema
from jdhapi.models import Article
from lxml import html
from rest_framework.response import Response
from weasyprint import HTML

from .logger import logger as get_logger

logger = get_logger()
article_to_ojs_schema = JSONSchema(filepath="article_to_ojs.json")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.OJS_API_KEY_TOKEN}",
}
OJS_API_URL = settings.OJS_API_URL
OJS_WEBSITE_URL = settings.OJS_WEBSITE_URL


def create_blank_submission():
    """
    Create a blank submission in OJS to get the submission_id for the article

    Returns: Response object from the OJS API with the submission_id in the response body
    """
    logger.info("creating a blank submission in OJS")

    url = f"{OJS_API_URL}/submissions"
    payload = {"commentsForTheEditors": "none", "locale": "en", "sectionId": 1}
    res = requests.post(url=url, headers=headers, json=payload)

    return res


def upload_manuscript_to_ojs(pid, submission_id, pdf_bytes):
    """
    Upload the pdf with the list of links to give access to the article (GitHub repository, Binder and JDH viewer)

    :param pid: The article pid
    :param submission_id: The OJS submission id to which the manuscript will be uploaded
    :param pdf_bytes: The pdf file in bytes to be uploaded to OJS
    """
    logger.info("uploading manuscript to OJS")

    url = f"{OJS_API_URL}/submissions/{submission_id}/files"
    headers_form_data = {"Authorization": f"Bearer {settings.OJS_API_KEY_TOKEN}"}
    files = {
        "file": (f"peer_review_{pid}.pdf", pdf_bytes, "application/pdf"),
    }
    data = {
        "fileStage": 2,  # 2 is for stage SUBMISSION_FILE_SUBMISSION
        "genreId": 1,  # 1 is for manuscript
    }

    res = requests.post(url=url, headers=headers_form_data, files=files, data=data)

    return res


def create_contributor_in_ojs(submission_id, publication_id, article: Article):
    """
    Create a contributor in OJS

    :param submission_id: The OJS submission id to which the contributor will be added
    :param publication_id: The OJS publication id to which the contributor will be added
    :param article: The article object
    """
    logger.info("creating the article contributor in OJS")

    primary_contact_id = 0

    url = f"{settings.OJS_API_URL}/submissions/{submission_id}/publications/{publication_id}/contributors"

    for author in article.abstract.authors.all():
        logger.info(f"Contributor {author.firstname} {author.lastname} creation in OJS")
        payload = {
            "affiliation": {"en": author.affiliation},
            "country": str(author.country),
            "email": author.email,
            "familyName": {"en": author.lastname},
            "fullName": f"{author.firstname} {author.lastname}",
            "givenName": {"en": author.firstname},
            "includeInBrowse": True,
            "locale": "en",
            "orcid": author.orcid,
            "preferredPublicName": {"en": ""},
            "publicationId": publication_id,
            "seq": 0,
            "userGroupId": 14,
            "userGroupName": {"en": "Author"},
        }
        res = requests.post(url=url, headers=headers, json=payload)
        logger.info(
            f"Contributor {author.firstname} {author.lastname} created with response: {res.json()}"
        )

        if article.abstract.contact_email == author.email:
            primary_contact_id = res.json().get("id", 0)

    return primary_contact_id


def assign_primary_contact_and_metadata(
    submission_id, publication_id, contributor_id, article
):
    """
    Assign the primary contact to the submission and add title, abstract and competing interests

    :param submission_id: The OJS submission id to which the contributor will be added
    :param publication_id: The OJS publication id to which the contributor will be added
    :param contributor_id: The OJS contributor id to be assigned as primary contact
    :param article: The article object
    """
    logger.info(
        "Assign the author as primary contact to the submission and add title, abstract and competingInterests"
    )

    url = f"{OJS_API_URL}/submissions/{submission_id}/publications/{publication_id}"
    payload = {
        "primaryContactId": contributor_id,
        "title": {"en": article.abstract.title},
        "abstract": {"en": article.abstract.abstract},
        "competingInterests": {"en": "I declare that I have no competing interests"},
    }

    res = requests.put(url=url, headers=headers, json=payload)

    return res


def submit_submission_to_ojs(submission_id):
    """
    Finalize the submission in OJS to move it from Incomplete stage to Submission stage

    :param submission_id: The OJS submission id to which the contributor will be added
    """
    logger.info("Submit the article to OJS")

    url = f"{OJS_API_URL}/submissions/{submission_id}/submit"
    payload = {"confirmCopyright": "true"}

    res = requests.put(url, headers=headers, json=payload)

    return res


def generate_pdf_for_submission(article):
    """
    Generate a PDF file with a list of links to give access to the article (GitHub repository, Binder and JDH viewer)

    :param article: The article object
    """
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


def get_active_submission_with_decision():
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title, author  and decision .
    """
    logger.info('Get submissions in peer review stage (stageId=3) from OJS formatted with id, link, title, author.')

    submissions_with_decisions = []

    try: 
        submissions = get_active_submissions()
        for submission in submissions:
            ojs_submission_id = submission.get("ojs_submission_id", 0)

            decision = get_decision_for_submission(ojs_submission_id)
            submission["decision"] = decision
            submissions_with_decisions.append(submission)

            logger.info(f"Active submissions in peer review stage with decisions : {submissions_with_decisions}")
        return submissions_with_decisions
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {"error": "An error occurred while retrieving submissions with decisions.", "details": str(e)},
            status=500
        )


def get_active_submissions():
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title and author.
    """
    logger.info('Get submissions in peer review stage (stageId=3) from OJS formatted with id, link, title, author.')

    url = f"{OJS_API_URL}/submissions?stageIds=3"
    submissions = []

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for item in response.json().get('items', []):
                stage_id = item.get('stageId', 0)
                id = item.get('id', 0)
                fulltitle = item.get('publications', [{}])[0].get("fullTitle", "No title")
                author = item.get('publications', [{}])[0].get("authorsString", "No author")

                submissions.append({
                    "ojs_submission_id": id,
                    "ojs_workflow_url": f"{OJS_WEBSITE_URL}/workflow/index/{id}/{stage_id}",
                    "title": fulltitle,
                    "author": author
                })

            logger.info(f"Active submissions in peer review stage : {submissions}")
            return submissions
        else:
            return Response(
                {
                    "error": "Unexpected error occurred while contacting OJS API.",
                    "status_code": response.status_code,
                },
                status=response.status_code
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to OJS API: {e}")
        return Response(
            {"error": "Failed to connect to OJS API.", "details": str(e)}, status=500
        )
    

def get_decision_for_submission(id: str):
    """
    Get list of OJS decisions for an article in peer review stage.
    """

    logger.info('Get decision for submission in OJS.')

    url = f"{OJS_API_URL}/submissions/{id}/decisions"

    try: 
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            decisions = response.json()
            logger.info(f"Decisions retrieved for submission {id}")
            return decisions

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to OJS API: {e}")
        return Response(
            {"error": "Failed to connect to OJS API.", "details": str(e)}, status=500
        )