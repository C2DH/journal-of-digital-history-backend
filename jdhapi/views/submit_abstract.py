from django.db import transaction
from django.core.mail import send_mail
from jdhapi.serializers import AbstractSerializer
from jsonschema.exceptions import ValidationError, SchemaError
from jdhapi.models import Abstract, Author, Dataset, CallOfPaper
from jdh.validation import JSONSchema
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .logger import logger as get_logger

# Initialize the logger object
logger = get_logger()

document_json_schema = JSONSchema(filepath="submit-abstract.json")


def get_default_body(subject, firstname, lastname):
    default_body = (
        "Dear "
        + firstname
        + " "
        + lastname
        + ",\n\n"
        + "Your submission "
        + subject
        + "has been sent to the managing editor of the "
        + "Journal of Digital History. "
        + "We will contact you back in a few days to discuss the feasibility "
        + "of your article, "
        + "as the JDH's layered articles "
        + "imply publishing a hermeneutics layer "
        + "and a data layer.\n\n"
        + "Best regard,\n\n"
        + "The JDH team."
    )
    return default_body


def send_mail_abstract_received(subject, sent_to, firstname, lastname):
    body = get_default_body(subject, firstname, lastname)
    try:
        send_mail(
            subject,
            body,
            "jdh.admin@uni.lu",
            [sent_to, "jdh.admin@uni.lu"],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def submit_abstract(request):
    try:
        data = validate_and_submit_abstract(request)
        return Response(data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        logger.exception("Validation error occurred.")
        response = Response(
            {"error": "ValidationError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )
        return response
    except SchemaError as e:
        logger.exception("Schema error occurred.")
        return Response(
            {"error": "SchemaError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )
    except (KeyError, IndexError) as e:
        logger.exception("Data invalid after validation")
        return Response(
            {"error": "KeyError", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
            content_type="application/json",
        )
    except Exception:
        logger.exception("An unexpected error occurred.")
        return Response(
            {
                "error": "InternalError",
                "message": "An unexpected error occurred. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )


def validate_and_submit_abstract(request):
    logger.info("Start JSON validation")
    with transaction.atomic():
        # Single transaction block for the entire function
        document_json_schema.validate(instance=request.data)

        logger.info("Handle call for paper")
        call_for_papers = request.data.get("callForPapers")

        if call_for_papers == "openSubmission":
            call_for_papers = ""

        if call_for_papers:
            logger.info(f"Processing call for paper: {call_for_papers}")
            try:
                call_paper = CallOfPaper.objects.get(folder_name=call_for_papers)
            except CallOfPaper.DoesNotExist:
                logger.error(f"Call for paper '{call_for_papers}' does not exist.")
                raise Exception(f"Call for paper '{call_for_papers}' does not exist.")

            abstract = Abstract(
                title=request.data.get("title"),
                abstract=request.data.get("abstract"),
                contact_affiliation="",
                contact_email="",
                contact_lastname="",
                contact_firstname="",
                language_preference=request.data.get("languagePreference"),
                consented=request.data.get("termsAccepted"),
                callpaper=call_paper,
            )
        else:
            abstract = Abstract(
                title=request.data.get("title"),
                abstract=request.data.get("abstract"),
                contact_affiliation="",
                contact_email="",
                contact_lastname="",
                contact_firstname="",
                language_preference=request.data.get("languagePreference"),
                consented=request.data.get("termsAccepted"),
            )
        abstract.save()
        logger.info(
            "Abstract details saved: title, abstract, language preference, and consent."
        )

        logger.info("Handle authors")
        authors = request.data["authors"]

        at_least_one_github_id = False
        at_least_one_primary_contact = False

        for author in authors:
            if author["githubId"]:
                at_least_one_github_id = True

            if author["primaryContact"]:
                at_least_one_primary_contact = True
                abstract.contact_affiliation = author["affiliation"]
                abstract.contact_email = author["email"]
                abstract.contact_lastname = author["lastname"]
                abstract.contact_firstname = author["firstname"]
                abstract.save()
                logger.info("Primary contact information updated")

            orcid = author.get("orcidUrl", "")
            author_instance, created = Author.objects.update_or_create(
                orcid=orcid,
                defaults={
                    "lastname": author["lastname"],
                    "firstname": author["firstname"],
                    "email": author["email"],
                    "affiliation": author["affiliation"],
                    "github_id": author.get("githubId", ""),
                    "bluesky_id": author.get("blueskyId", ""),
                    "facebook_id": author.get("facebookId", ""),
                },
            )
            abstract.authors.add(author_instance)

        if not at_least_one_github_id:
            raise ValidationError("At least one author must have a GitHub ID.")
        if not at_least_one_primary_contact:
            raise ValidationError(
                "At least one author must be marked as the primary contact."
            )

        logger.info("Authors saved")

        logger.info("Handle datasets")
        datasets = request.data.get("datasets", [])

        for dataset in datasets:
            new_dataset = Dataset(
                url=dataset["link"], description=dataset["description"]
            )
            new_dataset.save()
            abstract.datasets.add(new_dataset)

        logger.info("Datasets saved")

        logger.info("Start sending email confirmation")
        send_mail_abstract_received(
            abstract.title,
            abstract.contact_email,
            abstract.contact_firstname,
            abstract.contact_lastname,
        )
        logger.info("End sending email confirmation")

    logger.info("End submit abstract")
    abstract_serialized = AbstractSerializer(abstract)
    return abstract_serialized.data
