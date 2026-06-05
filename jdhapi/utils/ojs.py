from concurrent.futures import ThreadPoolExecutor, as_completed

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

REQUEST_TIMEOUT_SECONDS = 8
OJS_FETCH_WORKERS = 12


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
    Get active submissions with OJS decisions.
    """
    logger.info(
        "Get active submissions in peer review stage (stageId=3) from OJS with decisions"
    )

    submissions_with_decisions = []

    try:
        submissions = get_active_submissions()
        for submission in submissions:
            ojs_submission_id = submission.get("ojs_submission_id", 0)

            decision = get_decision_for_submission(ojs_submission_id)
            submission["decision"] = decision
            submissions_with_decisions.append(submission)

        return submissions_with_decisions
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {
                "error": "An error occurred while retrieving submissions with decisions.",
                "details": str(e),
            },
            status=500,
        )


def get_active_submission_with_timing():
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title, author  and decision .
    """
    logger.info(
        'Get submissions in peer review stage (stageId=3) from OJS formatted like with series like this [ontime, delay, order:"R1"]'
    )
    submissions_in_R1 = {"ontime": 0, "delay": 0, "order": "R1"}
    submissions_in_R2 = {"ontime": 0, "delay": 0, "order": "R2"}
    submissions_in_R3 = {"ontime": 0, "delay": 0, "order": "R3+"}
    submissions_with_timing = []

    try:
        # submissions = get_active_submissions_with_decision()
        submission_ids = get_active_submissions_ids()
        for id in submission_ids:
            url_submission = f"{OJS_API_URL}/submissions/{id}"

            response = requests.get(url_submission, headers=headers)
            if response.status_code == 200:
                submission = response.json()
                review_rounds = submission.get("reviewRounds") or []
                last_round = review_rounds[-1] if review_rounds else {}
                round = last_round.get("round", 0)
                status_id = last_round.get("statusId", 0)

            if round == 1:
                increase_round(submissions_in_R1, status_id)
            elif round == 2:
                increase_round(submissions_in_R2, status_id)
            elif round >= 3:
                increase_round(submissions_in_R3, status_id)

            submissions_with_timing = [
                submissions_in_R1,
                submissions_in_R2,
                submissions_in_R3,
            ]

        logger.info(
            f"Active submissions in peer review stage with decisions : {submissions_with_timing}"
        )
        return submissions_with_timing
    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {
                "error": "An error occurred while retrieving submissions with decisions.",
                "details": str(e),
            },
            status=500,
        )


def increase_round(submissions_in_round: [], status_id: int):
    if status_id == 10:
        submissions_in_round["ontime"] += 1
    else:
        submissions_in_round["delay"] += 1


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
    logger.info(
        "[get_active_submissions_by_stage] - Get submission sorted by peer review stage"
    )

    submissions_in_R1 = {
        "assign": 0,
        "awaiting": 0,
        "review": 0,
        "reviewer": 0,
        "revising": 0,
        "order": "R1",
    }
    submissions_in_R2 = {
        "assign": 0,
        "awaiting": 0,
        "review": 0,
        "reviewer": 0,
        "revising": 0,
        "order": "R2",
    }
    submissions_in_R3 = {
        "assign": 0,
        "awaiting": 0,
        "review": 0,
        "reviewer": 0,
        "revising": 0,
        "order": "R3+",
    }
    submissions_by_stage = []

    round = 0
    status_id = 0

    try:
        submission_ids = get_active_submissions_ids()
        for id in submission_ids:
            url_submission = f"{OJS_API_URL}/submissions/{id}"

            response = requests.get(url_submission, headers=headers)
            if response.status_code == 200:
                submission = response.json()
                review_rounds = submission.get("reviewRounds") or []
                last_round = review_rounds[-1] if review_rounds else {}
                round = last_round.get("round", 0)
                status_id = last_round.get("statusId", 0)

            status_id = is_author_revising(id, status_id)

            round_key = "R1" if round == 1 else "R2" if round == 2 else "R3+"
            match round_key:
                case "R1":
                    increase_round_per_stage(submissions_in_R1, status_id)
                case "R2":
                    increase_round_per_stage(submissions_in_R2, status_id)
                case "R3+":
                    increase_round_per_stage(submissions_in_R3, status_id)
                case _:
                    logger.error("No round is specified")

            submissions_by_stage = [
                submissions_in_R1,
                submissions_in_R2,
                submissions_in_R3,
            ]

        logger.info(
            f"Active submissions in peer review stage with decisions : {submissions_by_stage}"
        )
        return submissions_by_stage

    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {
                "error": "An error occurred while retrieving submissions with decisions.",
                "details": str(e),
            },
            status=500,
        )


def is_author_revising(id, status_id):
    try:
        url_decision = f"{OJS_API_URL}/submissions/{id}/decisions"
        response = requests.get(url_decision, headers=headers)

        if response.status_code == 200:
            decisions = response.json()
            last_decision = decisions[-1] if decisions else {}
            decision = last_decision.get("decision", 0)
            if decision == 4:
                return 100  # special code for author_revising
    except requests.exceptions.RequestException as e:
        logger.error(f"[is_author_revising] Failed to get decisions for {id}: {e}")

    return status_id


def _fetch_submission_and_status(submission_id):
    submission_url = f"{OJS_API_URL}/submissions/{submission_id}"
    decision_url = f"{OJS_API_URL}/submissions/{submission_id}/decisions"

    submission = None
    status_id_override = None

    try:
        res_submission = requests.get(
            submission_url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        res_submission.raise_for_status()
        submission = res_submission.json()
    except requests.exceptions.RequestException as e:
        logger.error(
            f"[get_active_submissions_by_stage_with_details] HTTP request failed for submission {submission_id}: {e}"
        )
        return submission_id, None, None

    # Keep current author-revising logic, but fetch in parallel worker
    try:
        res_decision = requests.get(
            decision_url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        if res_decision.status_code == 200:
            decisions = res_decision.json()
            last_decision = decisions[-1] if decisions else {}
            if last_decision.get("decision", 0) == 4:
                status_id_override = 100
    except requests.exceptions.RequestException as e:
        logger.error(
            f"[get_active_submissions_by_stage_with_details] Decision request failed for submission {submission_id}: {e}"
        )

    return submission_id, submission, status_id_override


def get_active_submissions_by_stage_with_details():
    """
    Get list of OJS peer review articles details for each stages.
    It will return an object type like this :
    [
        {
            key: 'assign-R1',
            articles: [
            {
                authors: string,
                title: string,
                url: string,
                pid: string,
                substatus: ['thanked', 'thanked', 'overdue'],
            },
            ...
            ],
        },
        {
            key: 'assign-R2',
            articles: [...],
        },
        ...
    ]

    List of the stages for key :
    - assign
    - awaiting
    - review
    - reviewer
    - revising
    """
    logger.info(
        "[get_active_submissions_by_stage_with_details] - Get list of detail articles for each peer review stage"
    )

    submissions_by_stage_round = [
        {"key": "assign-R1", "articles": []},
        {"key": "awaiting-R1", "articles": []},
        {"key": "review-R1", "articles": []},
        {"key": "reviewer-R1", "articles": []},
        {"key": "revising-R1", "articles": []},
        {"key": "assign-R2", "articles": []},
        {"key": "awaiting-R2", "articles": []},
        {"key": "review-R2", "articles": []},
        {"key": "reviewer-R2", "articles": []},
        {"key": "revising-R2", "articles": []},
        {"key": "assign-R3", "articles": []},
        {"key": "awaiting-R3", "articles": []},
        {"key": "review-R3", "articles": []},
        {"key": "reviewer-R3", "articles": []},
        {"key": "revising-R3", "articles": []},
    ]

    try:
        submission_ids = get_active_submissions_ids()
        if not isinstance(submission_ids, list):
            return submission_ids

        # Parallel HTTP fetch (submission + decision)
        fetched = []
        with ThreadPoolExecutor(max_workers=OJS_FETCH_WORKERS) as pool:
            futures = {
                pool.submit(_fetch_submission_and_status, sid): sid
                for sid in submission_ids
            }
            for f in as_completed(futures):
                sid, submission, status_override = f.result()
                if submission:
                    fetched.append((sid, submission, status_override))

        # Build title set for one-shot fallback lookup
        titles = set()
        parsed_rows = []
        for sid, submission, status_override in fetched:
            try:
                publication = (submission.get("publications") or [{}])[0]
                fulltitle = (publication.get("fullTitle") or {}).get("en", "No title")
                author = publication.get("authorsString", "No author")
                review_assignments = submission.get("reviewAssignments") or []
                review_rounds = submission.get("reviewRounds") or []
                last_round = review_rounds[-1] if review_rounds else {}
                round_value = last_round.get("round", 0)
                status_id = status_override or last_round.get("statusId", 0)
                url_workflow = submission.get("urlWorkflow")

                parsed_rows.append(
                    {
                        "id": submission.get("id", sid),
                        "title": fulltitle,
                        "author": author,
                        "review_assignments": review_assignments,
                        "round": round_value,
                        "status_id": status_id,
                        "url_workflow": url_workflow,
                    }
                )
                titles.add(fulltitle)
            except Exception as e:
                logger.error(
                    f"[get_active_submissions_by_stage_with_details] Failed to parse submission data for id {sid}: {e}"
                )

        # One-shot DB fetch by OJS id
        articles_by_sid = {
            a.ojs_submission_id: a
            for a in Article.objects.filter(
                ojs_submission_id__in=[row["id"] for row in parsed_rows]
            ).select_related("abstract")
        }

        # One-shot fallback by title
        missing_titles = [
            row["title"] for row in parsed_rows if row["id"] not in articles_by_sid
        ]
        fallback_by_title = {}
        if missing_titles:
            for a in (
                Article.objects.filter(abstract__title__in=missing_titles)
                .select_related("abstract")
            ):
                fallback_by_title.setdefault(a.abstract.title, a)

        # Build response
        for row in parsed_rows:
            article_db = articles_by_sid.get(row["id"]) or fallback_by_title.get(row["title"])
            pid = article_db.abstract.pid if article_db else None

            article = {
                "pid": pid,
                "authors": row["author"],
                "title": row["title"],
                "url": row["url_workflow"],
                "substatus": assign_substatus(row["review_assignments"]),
            }
            find_right_stage_and_round(
                submissions_by_stage_round, row["round"], row["status_id"], article
            )

        return submissions_by_stage_round

    except Exception as e:
        logger.error(f"Error while retrieving submissions with decisions: {e}")
        return Response(
            {
                "error": "An error occurred while retrieving submissions with decisions.",
                "details": str(e),
            },
            status=500,
        )


def find_right_stage_and_round(submissions, round, status_id, article):
    # Keep R3 label to match initialized keys assign-R3, etc.
    round_label = "R1" if round == 1 else "R2" if round == 2 else "R3"

    match status_id:
        case 6 | 15:
            stage = "assign"
        case 7:
            stage = "awaiting"
        case 10:
            stage = "review"
        case 1 | 2 | 4 | 8 | 9:
            stage = "reviewer"
        case 100:
            stage = "revising"
        case _:
            logger.error("[find_right_stage_and_round] - Status Id is not managed.")
            return

    key = f"{stage}-{round_label}"
    entry = next((s for s in submissions if s["key"] == key), None)
    if entry is not None:
        entry["articles"].append(article)
    else:
        logger.error(f"[find_right_stage_and_round] - Key {key} not found.")


def increase_round_per_stage(submissions_in_round, status_id):
    match status_id:
        case 6 | 15:
            submissions_in_round["assign"] += 1
        case 7:
            submissions_in_round["awaiting"] += 1
        case 10:
            submissions_in_round["review"] += 1
        case 1 | 2 | 4 | 8 | 9:
            submissions_in_round["reviewer"] += 1
        case 100:
            submissions_in_round["revising"] += 1
        case _:
            logger.error("[increase_round_per_stage] - Status Id is not managed.")
            

def assign_substatus(review_assignments):
    """
    Create an array of substatus eg.['thanked', 'thanked', 'accepted'].
    """
    substatuses = []

    for r in review_assignments:
        status_id = r.get("statusId", 0)

        match status_id:
            case 0:
                substatuses.append("pending")
            case 1:
                substatuses.append("declined")
            case 4 | 6:
                substatuses.append("overdue")
            case 5:
                substatuses.append("accepted")
            case 7:
                substatuses.append("submitted")
            case 8:
                substatuses.append("confirmed")
            case 9:
                substatuses.append("thanked")
            case 10:
                substatuses.append("cancelled")
            case 11:
                substatuses.append("resent")
            case 12:
                substatuses.append("viewed")
            case _:
                logger.error("[assign_substatus] - Status Id is not managed.")
                return

    return substatuses


def get_active_submissions():
    """
    Get list of OJS peer review articles with oj_submission_id, ojs_workflow_url, title and author.
    """
    logger.info(
        "Get submissions in peer review stage (stageId=3) from OJS formatted with id, link, title, author."
    )

    url = f"{OJS_API_URL}/submissions?stageIds=3"
    submissions = []

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for item in response.json().get("items", []):
                stage_id = item.get("stageId", 0)
                id = item.get("id", 0)
                fulltitle = item.get("publications", [{}])[0].get(
                    "fullTitle", "No title"
                )
                author = item.get("publications", [{}])[0].get(
                    "authorsString", "No author"
                )

                submissions.append(
                    {
                        "ojs_submission_id": id,
                        "ojs_workflow_url": f"{OJS_WEBSITE_URL}/workflow/index/{id}/{stage_id}",
                        "title": fulltitle,
                        "author": author,
                    }
                )

            # logger.info(f"Active submissions in peer review stage : {submissions}")
            return submissions
        else:
            return Response(
                {
                    "error": "Unexpected error occurred while contacting OJS API.",
                    "status_code": response.status_code,
                },
                status=response.status_code,
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
    logger.info(
        "Get submissions in peer review stage (stageId=3) from OJS all the current article OJS IDs."
    )

    url = f"{OJS_API_URL}/submissions?stageIds=3"
    ids = []

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for item in response.json().get("items", []):
                id = item.get("id", 0)

                ids.append(id)

            # logger.info(f"Active submissions in peer review stage : {submissions}")
            return ids
        else:
            return Response(
                {
                    "error": "Unexpected error occurred while contacting OJS API.",
                    "status_code": response.status_code,
                },
                status=response.status_code,
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

    logger.info("Get decision for submission in OJS.")

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
