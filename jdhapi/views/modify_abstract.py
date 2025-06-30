from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from jdhapi.models import Abstract
from jdhapi.forms import EmailConfigurationForm
from jdh.validation import JSONSchema
from jsonschema.exceptions import ValidationError, SchemaError
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .logger import logger as get_logger

# Initialize the logger object
logger = get_logger()

document_json_schema = JSONSchema(filepath="contact-form.json")


def sendmail(subject, body, sent_to):
    try:
        send_mail(
            subject,
            body,
            "marion.salaun@uni.lu",
            ["marion.salaun@uni.lu"],
            # "jdh.admin@uni.lu",
            # [sent_to, "jdh.admin@uni.lu"],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def modify_abstract(request, pid):

    try:
        data = change_abstract_status(request, pid)
        return Response(
            {"message": "Abstract updated successfully.", "data": data},
            status=status.HTTP_200_OK,
        )
    except ValidationError as e:
        logger.error(f"JSON schema validation failed: {e}")
        return Response(
            {"error": "Invalid data format", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
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


def change_abstract_status(request, pid):
    logger.info("Start JSON validation")
    with transaction.atomic():

        document_json_schema.validate(instance=request.data)

        try:
            logger.info("Retrieve abstract according to PID.")
            if not pid:
                logger.error("No PID provided in request data.")
                raise ValidationError({"error": "PID is required."})
            abstract = get_object_or_404(Abstract, pid=pid)
        except Abstract.DoesNotExist:
            logger.error(f"Abstract with PID {pid} does not exist.")
            raise ValidationError({"error": "Abstract not found."})

        to = request.data.get("to", abstract.contact_email)
        print("🚀 ~ file: modify_abstract.py:99 ~ to:", to)
        subject = request.data.get("subject", abstract.title)
        body = request.data.get("message", "")
        new_status = request.data.get("status", "").upper()

        email = EmailConfigurationForm(request.data)
        if not email.is_valid():
            logger.error(f"Email form invalid: {email.errors}")
            raise Exception({"error": "Invalid email data", "details": email.errors})

        email_clean = email.cleaned_data
        subject = email_clean.get("subject", subject)
        body = email_clean.get("body", body)

        try:
            if abstract.status == Abstract.Status.SUBMITTED:
                sendmail(subject, body, to)
                logger.info(f"Mail sent to {to} for abstract {pid} (SUBMITTED).")
                if new_status == Abstract.Status.DECLINED:
                    abstract.declined()
                    logger.info(f"Abstract {pid} declined.")
                elif new_status == Abstract.Status.ABANDONED:
                    abstract.abandoned()
                    logger.info(f"Abstract {pid} abandoned.")
                elif new_status == Abstract.Status.ACCEPTED:
                    abstract.accepted()
                    logger.info(f"Abstract {pid} accepted.")

            elif abstract.status == Abstract.Status.ACCEPTED:
                sendmail(subject, body, to)
                logger.info(f"Mail sent to {to} for abstract {pid} (ACCEPTED).")
                if new_status == Abstract.Status.ABANDONED:
                    abstract.abandoned()
                    logger.info(f"Abstract {pid} abandoned.")
                elif new_status == Abstract.Status.SUSPENDED:
                    abstract.suspended()
                    logger.info(f"Abstract {pid} suspended.")

            abstract.save()
            logger.info(f"Abstract {pid} saved after status update.")

        except Exception as e:
            logger.error(f"Error processing status of the abstract {pid}: {e}")
            raise Exception({"error": "ProcessingError", "message": str(e)})

        return {
            "pid": abstract.pid,
            "title": abstract.title,
            "new_status": abstract.status,
        }
