import marko
import requests
from django.conf import settings
from django.template.loader import render_to_string
from jdh.validation import JSONSchema
from jdhapi.models import Article
from lxml import html
from weasyprint import HTML

from .logger import logger as get_logger

logger = get_logger()
article_to_ojs_schema = JSONSchema(filepath="article_to_ojs.json")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.OJS_API_KEY_TOKEN}",
}
OJS_API_URL = settings.OJS_API_URL


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
