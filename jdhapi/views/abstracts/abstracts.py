from typing import ClassVar

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework import filters, generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from jdhapi.models import Abstract
from jdhapi.serializers.abstract import AbstractSerializer, CreateAbstractSerializer
from jdhapi.views.abstracts.status_handlers import (
    AbandonedHandler,
    AcceptedHandler,
    DeclinedHandler,
    PublishedHandler,
    SubmittedHandler,
    SuspendedHandler,
)


class V2Serializer(Serializer):
    token = ReCaptchaV2Field()


class AbstractList(generics.ListCreateAPIView):
    queryset = Abstract.objects.all()
    permission_classes: ClassVar[list[object]] = [IsAdminUser]
    serializer_class = AbstractSerializer
    filter_backends: ClassVar[list[object]] = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields: ClassVar[list[str]] = [
        "id",
        "pid",
        "title",
        "callpaper",
        "callpaper__title",
        "submitted_date",
        "validation_date",
        "language_preference",
        "contact_affiliation",
        "contact_lastname",
        "contact_firstname",
        "consented",
        "authors",
        "article__issue",
    ]
    ordering_fields: ClassVar[list[str]] = [
        "id",
        "title",
        "callpaper",
        "callpaper__title",
        "submitted_date",
        "validation_date",
        "status",
        "contact_lastname",
        "contact_firstname",
        "contact_affiliation",
    ]
    search_fields: ClassVar[list[str]] = [
        "title",
        "pid",
        "contact_lastname",
        "contact_firstname",
        "authors__lastname",
        "authors__firstname",
    ]

    def get_queryset(self):
        """
        Override to filter by 'status' if provided in query params.
        """
        queryset = Abstract.objects.all()
        qs = super().filter_queryset(queryset)

        status_param = self.request.query_params.get("status")

        if status_param:
            if status_param.startswith("!"):
                status_value = status_param[1:]
                qs = qs.exclude(status=status_value)
            else:
                qs = qs.filter(status=status_param)

        return qs

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.serializer_class = CreateAbstractSerializer
        super().create(request, *args, **kwargs)
        return Response({"received data": request.data})


class AbstractDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Abstract.objects.all()
    serializer_class = AbstractSerializer
    lookup_field = "pid"


class AbstractStatus(APIView):
    permission_classes: ClassVar[list[object]] = [IsAdminUser]
    STATUS_HANDLERS: ClassVar[dict[str, object]] = {
        "SUBMITTED": SubmittedHandler(),
        "ACCEPTED": AcceptedHandler(),
        "DECLINED": DeclinedHandler(),
        "ABANDONED": AbandonedHandler(),
        "SUSPENDED": SuspendedHandler(),
        "PUBLISHED": PublishedHandler()
    }

    def patch(self, request, pid):
        abstract = get_object_or_404(Abstract, pid=pid)
        new_status = request.data.get("status")

        handler = self.STATUS_HANDLERS.get(new_status)
        if handler:
            return handler.handle(abstract)
        return Response({"error": "Invalid status"}, status=400)
