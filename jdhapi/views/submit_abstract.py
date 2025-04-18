from django.db import transaction
from django.core.mail import send_mail
from jsonschema.exceptions import ValidationError, SchemaError
from jdhapi.models import Abstract, Author, Dataset, CallOfPaper
from jdhapi.serializers import AbstractSerializer
from jdh.validation import JSONSchema
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .logger import logger as get_logger

# Initialize the logger object
logger = get_logger()

document_json_schema = JSONSchema(filepath='submit-abstract.json')

def getDefaultBody(subject, firstname, lastname):
    defaultBody = "Dear " + firstname + " " + lastname + ',' + '\n\n' + "Your submission " + subject + " has been sent to the managing editor of the Journal of Digital History. We will contact you back in a few days to discuss the feasibility of your article, as the JDH's layered articles imply to publish an hermeneutics and a data layer." + "\n\n" + "Best regard," + "\n\n" + "The JDH team."
    return defaultBody


def sendmailAbstractReceived(subject, sent_to, firstname, lastname):
    body = getDefaultBody(subject, firstname, lastname)
    try:
        send_mail(
            subject,
            body,
            'jdh.admin@uni.lu',
            [sent_to, 'jdh.admin@uni.lu'],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def SubmitAbstract(request):
    try:
        logger.info('Start JSON validation')
        with transaction.atomic():  # Single transaction block for the entire function
            try:
                document_json_schema.validate(instance=request.data)
                logger.info('Abstract validated')
            except ValidationError as err:
                logger.exception("Validation error in request data.")
                raise ValidationError(f"Invalid data: {err.message}", details=err.schema)
            except SchemaError as err:
                logger.exception("Schema error in JSON validation.")
                raise ValidationError(f"Schema issue: {err.message}")

            logger.info('Handle contact information')
            contact_list = request.data.get("contact", [])
            if not isinstance(contact_list, list) or not contact_list:
                raise ValidationError("Contact information is required and must be a non-empty list.")

            contact = contact_list[0]
            required_contact_fields = ['firstname', 'lastname', 'email', 'affiliation']
            missing_contact_fields = [field for field in required_contact_fields if field not in contact]
            if missing_contact_fields:
                raise ValidationError(f"Missing required contact fields: {', '.join(missing_contact_fields)}")

            logger.info('Handle call for paper')
            call_for_papers = request.data.get("callForPapers")
            if call_for_papers:
                logger.info(f'Processing call for paper: {call_for_papers}')
                try:
                    call_paper = CallOfPaper.objects.get(folder_name=call_for_papers)
                except CallOfPaper.DoesNotExist:
                    logger.error(f"Call for paper '{call_for_papers}' does not exist.")
                    raise NotFoundError(f"Call for paper '{call_for_papers}' does not exist.")

                abstract = Abstract(
                    title=request.data.get("title"),
                    abstract=request.data.get("abstract"),
                    contact_affiliation=contact.get("affiliation"),
                    contact_email=contact.get("email"),
                    contact_lastname=contact.get("lastname"),
                    contact_firstname=contact.get("firstname"),
                    language_preference=request.data.get("languagePreference"),
                    consented=request.data.get("termsAccepted"),
                    callpaper=call_paper
                )
            else:
                abstract = Abstract(
                    title=request.data.get("title"),
                    abstract=request.data.get("abstract"),
                    contact_affiliation=contact.get("affiliation"),
                    contact_email=contact.get("email"),
                    contact_lastname=contact.get("lastname"),
                    contact_firstname=contact.get("firstname"),
                    language_preference=request.data.get("languagePreference"),
                    consented=request.data.get("termsAccepted")
                )
            abstract.save()
            logger.info('Basic abstract information saved')

            logger.info('Handle authors')
            authors = request.data.get('authors', [])
            if not isinstance(authors, list):
                raise ValidationError("Authors must be provided as a list.")

            at_least_one_github_id = False
            for author in authors:
                required_author_fields = ['lastname', 'firstname', 'email', 'affiliation', 'orcidUrl']
                missing_author_fields = [field for field in required_author_fields if field not in author]
                if missing_author_fields:
                    raise ValidationError(f"Missing required author fields: {', '.join(missing_author_fields)}")

                if author.get('githubId'):
                    at_least_one_github_id = True

                orcid = author.get('orcidUrl', '')
                author_instance, created = Author.objects.update_or_create(
                    orcid=orcid,
                    defaults={
                        'lastname': author['lastname'],
                        'firstname': author['firstname'],
                        'email': author['email'],
                        'affiliation': author['affiliation'],
                        'github_id': author.get('githubId', ''),
                        'bluesky_id': author.get('blueskyId', ''),
                        'facebook_id': author.get('facebookId', '')
                    }
                )
                abstract.authors.add(author_instance)

            if not at_least_one_github_id:
                raise ValidationError("At least one author must have a GitHub ID.")
            logger.info('Authors saved')

            logger.info('Handle datasets')
            datasets = request.data.get('datasets', [])
            if not isinstance(datasets, list):
                raise ValidationError("Datasets must be provided as a list.")

            for dataset in datasets:
                if 'link' not in dataset or 'description' not in dataset:
                    raise ValidationError('Each dataset must include "link" and "description" fields.')

                new_dataset = Dataset(
                    url=dataset['link'],
                    description=dataset['description']
                )
                new_dataset.save()
                abstract.datasets.add(new_dataset)
            logger.info('Datasets saved')

            logger.info("Start sending email confirmation")
            sendmailAbstractReceived(
                abstract.title,
                abstract.contact_email,
                abstract.contact_firstname,
                abstract.contact_lastname
            )
            logger.info("End sending email confirmation")

        logger.info("End submit abstract")
        serializer = AbstractSerializer(abstract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        logger.exception("Validation error occurred.")
        return Response({
            'error': 'ValidationError',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        return Response({
            'error': 'InternalError',
            'message': 'An unexpected error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)