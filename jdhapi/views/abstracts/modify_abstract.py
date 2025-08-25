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
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from ..logger import logger as get_logger

logger = get_logger()

contact_form_schema = JSONSchema(filepath="contact_form.json")


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def modify_abstract(request, pid):
    """
    PATCH /api/abstracts/status

    Endpoint to modify the status of an abstract identified by its PID.
    It sends an email notification to the contact email of the abstract.
    Requires admin permissions.
    """

    try:
        data = change_abstract_status_with_email(request, pid)
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
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
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


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def modify_abstracts(request, pids):
    """
    PATCH /api/abstracts/status

    Endpoint to modify the status of one or several abstract identified by its PID.
    Send no email notification.
    Requires admin permissions.
    """

    try:
        data = change_abstract_status(request, pids)
        return Response(
            {"message": "Abstracts updated successfully.", "data": data},
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
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json",
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


def send_mail_to_contact(request, abstract, status):
    """
    Sends an email notification to the contact associated with an abstract.
    Args:
        request: containing email data (from, to, subject, message).
        abstract: containing contact information and title.
        status: status of the abstract
    """
    sender = request.data.get("from", "jdh.admin@uni.lu")
    receiver = request.data.get("to", abstract.contact_email)
    subject = request.data.get("subject", abstract.title)
    body = request.data.get("message", "")

    email = EmailConfigurationForm(request.data)
    if not email.is_valid():
        logger.error(f"Email form invalid: {email.errors}")
        raise Exception({"error": "Invalid email data", "details": email.errors})

    email_clean = email.cleaned_data
    subject = email_clean.get("subject", subject)
    body = email_clean.get("body", body)
    logger.info("Mail prepared to be sent.")

    try:
        send_mail(
            subject,
            body,
            sender,
            [receiver, "jdh.admin@uni.lu"],
            fail_silently=False,
        )
        logger.info(f"Mail sent to {receiver} for abstract {abstract.pid} ({status}).")
    except Exception as e:
        raise Exception({"error": "send_mail error", "message": str(e)})


def change_abstract_status_with_email(request, pid):
    """
    Change the abstract status and send email notification.
    Args:
        request: containing email data (from, to, subject, message).
        pid: PID of the abstract to be modified.
    """
    logger.info("Change abstract status with email notification")
    logger.info("Start JSON validation")
    with transaction.atomic():

        contact_form_schema.validate(instance=request.data)

        try:
            logger.info("Retrieve abstract according to PID.")
            if not pid:
                logger.error("No PID provided in request data.")
                raise ValidationError({"error": "PID is required."})
            abstract = get_object_or_404(Abstract, pid=pid)
        except Abstract.DoesNotExist:
            logger.error(f"Abstract with PID {pid} does not exist.")
            raise Exception({"error": "Abstract not found."})

        new_status = request.data.get("status", "").upper()

        try:
            if abstract.status == Abstract.Status.SUBMITTED:
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

                if new_status == Abstract.Status.ABANDONED:
                    abstract.abandoned()
                    logger.info(f"Abstract {pid} abandoned.")
                elif new_status == Abstract.Status.SUSPENDED:
                    abstract.suspended()
                    logger.info(f"Abstract {pid} suspended.")

            abstract.save()
            logger.info(f"Abstract {pid} saved after status update.")
            send_mail_to_contact(request, abstract, new_status)

        except Exception as e:
            logger.error(f"Error processing status of the abstract {pid}: {e}")
            raise Exception({"error": "ProcessingError", "message": str(e)})

        return {
            "pid": abstract.pid,
            "title": abstract.title,
            "new_status": abstract.status,
        }


def change_abstract_status(request, pids):
    """
    Change abstract(s) status(es) with no notification.
    Args:
        request: containing email data (from, to, subject, message).
        pids: PID(s) of the abstract(s) to be modified.
    """
    logger.info("Change abstract status")
    logger.info("Start JSON validation")
    with transaction.atomic():

        # need to be updated to use the correct schema
        # contact_form_schema.validate(instance=request.data)

        try:
            logger.info("Retrieve abstract(s) according to PID(s).")
            if not pids:
                logger.error("No PID provided in request data.")
                raise ValidationError({"error": "At least one PID is required."})

            abstracts = Abstract.objects.filter(pid__in=pids)
            if not abstracts.exists():
                logger.error(f"No Abstracts found for PIDs {pids}.")
                raise Exception({"error": "Abstract(s) not found."})

        except Abstract.DoesNotExist:
            logger.error(f"Abstracts with PID(s) {pids} do not exist.")
            raise Exception({"error": "Abstract(s) not found."})

        new_status = request.data.get("status", "").upper()
        updated_abstracts = []

        for abstract in abstracts:
            abstract.status = new_status
            abstract.save()
            updated_abstracts.append(
                {
                    "pid": abstract.pid,
                    "title": abstract.title,
                    "new_status": abstract.status,
                }
            )
            logger.info(f"Abstract {abstract.pid} status updated to {new_status}.")

    return updated_abstracts
