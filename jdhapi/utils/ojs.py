import datetime as dt

import marko
import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
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


def get_active_submissions_with_decision():
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title, author and decision .
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

            # logger.info(f"Active submissions in peer review stage with decisions : {submissions_with_decisions}")
        return submissions_with_decisions
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {"error": "An error occurred while retrieving submissions with decisions.", "details": str(e)},
            status=500
        )

def get_active_submission_with_timing(): 
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title, author  and decision .
    """
    logger.info('Get submissions in peer review stage (stageId=3) from OJS formatted like with series like this [ontime, delay, order:"R1"]')
    submissions_in_R1 = {'ontime': 0, 'delay': 0, 'order': 'R1'}
    submissions_in_R2 = {'ontime': 0, 'delay': 0, 'order': 'R2'}
    submissions_in_R3 = {'ontime': 0, 'delay': 0, 'order': 'R3+'}
    submissions_with_timing = []

    try: 
        submissions = get_active_submissions_with_decision()
        for submission in submissions:
            round = submission.get("decision", [{}])[-1].get("round") or 1
            raw_date = submission.get("decision", [{}])[-1].get("dateDecided")
            date = dt.datetime.fromisoformat(raw_date) 
            if raw_date :
                parsed = dt.datetime.fromisoformat(raw_date)
                date = parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
            else :
                date = timezone.now()

            if round == 1 : 
                increase_round(submissions_in_R1, date)
            elif round == 2 :
                increase_round(submissions_in_R2, date)
            elif round >= 3 :
                increase_round(submissions_in_R3, date)
            
            submissions_with_timing = [submissions_in_R1, submissions_in_R2, submissions_in_R3]

        logger.info(f"Active submissions in peer review stage with decisions : {submissions_with_timing}")
        return submissions_with_timing
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {"error": "An error occurred while retrieving submissions with decisions.", "details": str(e)},
            status=500
        )
    
def increase_round(submissions_in_round, date):
        if (date + dt.timedelta(days=30)) > timezone.now() :
            submissions_in_round['ontime'] += 1
        else : 
            submissions_in_round['delay'] += 1

def get_active_submissions_by_stage():
    """
    Get list of OJS peer review articles sorted by following stages :
    - Assign reviewer (assign)
    - Awaiting reviewer response (awaiting)
    - Review in progress (review)
    - Reviewer decision (reviewer)
    - Author revising (revising)
    Data will be returned this way : [assign:int, awaiting: int, review: int, reviewer: int, revising: int, order: 'R1']
    It will be done for R1, R2 and R3+ rounds of peer review.
    """
    logger.info('Get submissions in peer review stage (stageId=3) from OJS formatted with id, link, title, author.')

    submissions_in_R1 = {'assign':0, 'awaiting': 0, 'review': 0, 'reviewer': 0, 'revising': 0, 'order': 'R1'}
    submissions_in_R2 = {'assign':0, 'awaiting': 0, 'review': 0, 'reviewer': 0, 'revising': 0, 'order': 'R2'}
    submissions_in_R3 = {'assign':0, 'awaiting': 0, 'review': 0, 'reviewer': 0, 'revising': 0, 'order': 'R3+'}
    submissions_by_stage = []

    decision = 0
    round = 0
    status_id = 0

    try: 
        submission_ids = get_active_submissions_ids()
        for id in submission_ids:
            url_decision = f"{OJS_API_URL}/submissions/{id}/decisions"
            response = requests.get(url_decision, headers=headers)

            if response.status_code == 200:
                decisions = response.json()
                last_decision = decisions[-1] if decisions else {}
                decision = last_decision.get('decision', 0)
                round = last_decision.get('round', 0)

            if decision == 4 : 
                match round : 
                    case 'R1':
                        increase_round_per_stage(submissions_in_R1, 100)
                    case 'R2':
                        increase_round_per_stage(submissions_in_R2, 100)
                    case 'R3+':
                        increase_round_per_stage(submissions_in_R3, 100)
                    case _:
                        logger.error('No round is specified')
      
            url_submission = f"{OJS_API_URL}/submissions/{id}"

            response = requests.get(url_submission, headers=headers)
            if response.status_code == 200:
                submission = response.json()
                review_rounds = submission.get('reviewRounds') or []
                last_round = review_rounds[-1] if review_rounds else {}
                round = last_round.get('round', 0)
                status_id = last_round.get('statusId', 0)

            round_key = 'R1' if round == 1 else 'R2' if round == 2 else 'R3+'
            match round_key : 
                case 'R1':
                    increase_round_per_stage(submissions_in_R1, status_id)
                case 'R2':
                    increase_round_per_stage(submissions_in_R2, status_id)
                case 'R3+':
                    increase_round_per_stage(submissions_in_R3, status_id)
                case _:
                    logger.error('No round is specified')
      
            submissions_by_stage = [submissions_in_R1, submissions_in_R2, submissions_in_R3]

        logger.info(f"Active submissions in peer review stage with decisions : {submissions_by_stage}")
        return submissions_by_stage
    
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {"error": "An error occurred while retrieving submissions with decisions.", "details": str(e)},
            status=500
        )
    
def increase_round_per_stage(submissions_in_round, status_id):
    match status_id:
        case 6 | 16:
            submissions_in_round['assign'] += 1
        case 7:
            submissions_in_round['awaiting'] += 1
        case 5:
            submissions_in_round['review'] += 1
        case 1 | 2 | 4 | 8 | 9:
            submissions_in_round['reviewer'] += 1
        case 100 :
            submissions_in_round['revising'] += 1
        case _:
            logger.error('[increase_round_per_stage] - Status Id is not managed.')



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
                    "author": author,
                
                })

            # logger.info(f"Active submissions in peer review stage : {submissions}")
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
    
def get_active_submissions_ids():
    """
    Get list of OJS peer review articles ids.
    """
    logger.info('Get submissions in peer review stage (stageId=3) from OJS all the current article OJS IDs.')

    url = f"{OJS_API_URL}/submissions?stageIds=3"
    ids = []

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for item in response.json().get('items', []):
                id = item.get('id', 0)

                ids.append(id)

            # logger.info(f"Active submissions in peer review stage : {submissions}")
            return ids
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