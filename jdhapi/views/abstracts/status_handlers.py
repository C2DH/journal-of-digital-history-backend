import logging

from rest_framework.response import Response

logger = logging.getLogger(__name__)


class StatusHandler:
    def handle(self, abstract):
        raise NotImplementedError


class SubmittedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status SUBMITTED pid=%s", abstract.pid)
        abstract.submitted()
        return Response(
            {"status": "Submitted set.", "pid": abstract.pid}
        )


class AcceptedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status ACCEPTED pid=%s", abstract.pid)
        abstract.accepted()
        return Response(
            {"status": "Accepted set.", "pid": abstract.pid}
        )


class DeclinedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status DECLINED pid=%s", abstract.pid)
        abstract.declined()
        return Response(
            {"status": "Declined set.", "pid": abstract.pid}
        )


class AbandonedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status ABANDONED pid=%s", abstract.pid)
        abstract.abandoned()
        return Response(
            {"status": "Abandoned set.", "pid": abstract.pid}
        )


class SuspendedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status SUSPENDED pid=%s", abstract.pid)
        abstract.suspended()
        return Response(
            {"status": "Suspended set.", "pid": abstract.pid}
        )


class PublishedHandler(StatusHandler):
    def handle(self, abstract):
        logger.info("Setting status PUBLISHED pid=%s", abstract.pid)
        abstract.status = abstract.Status.PUBLISHED
        abstract.save()
        return Response(
            {"status": "Published set.", "pid": abstract.pid}
        )
