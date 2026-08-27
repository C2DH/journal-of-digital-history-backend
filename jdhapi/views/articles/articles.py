from typing import ClassVar

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from jdhapi.filter.article import (
    IsAuthenticatedPermission,
    IsStaffFilter,
)
from jdhapi.models import Article
from jdhapi.serializers.article import ArticleSerializer
from jdhapi.views.articles.status_handlers import (
    CopyEditingHandler,
    PeerReviewHandler,
    PublishedHandler,
    RejectedHandler,
    TechnicalReviewHandler,
)


class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends: ClassVar[list[object]] = [
        IsStaffFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields: ClassVar[list[str]] = [
        "issue",
        "abstract",
        "status",
        "tags",
        "authors",
        "copyright_type",
        "abstract__callpaper",
    ]
    ordering_fields: ClassVar[list[str]] = [
        "issue__publication_date",
        "publication_date",
        "abstract__title",
        "abstract__pid",
    ]
    ordering: ClassVar[list[str]] = ["-issue__publication_date", "-publication_date"]
    search_fields: ClassVar[list[str]] = [
        "abstract__title",
        "abstract__pid",
        "abstract__contact_lastname",
        "abstract__contact_firstname",
        "abstract__authors__lastname",
        "abstract__authors__firstname",
    ]

    def get_queryset(self):
        """
        Optionally restricts the returned articles to a given issue,
        by filtering against a `pid` query parameter in the URL.
        """
        queryset = super().get_queryset()
        pid = self.request.query_params.get("pid")
        if pid is not None:
            queryset = queryset.filter(issue__pid=pid)
        return queryset

    def filter_queryset(self, queryset):
        # Apply DRF filters
        qs = super().filter_queryset(queryset)
        return qs


class ArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes: ClassVar[list[object]] = [IsAuthenticatedPermission]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = "abstract__pid"


class ArticleStatus(APIView):
    permission_classes: ClassVar[list[object]] = [IsAdminUser]
    STATUS_HANDLERS: ClassVar[dict[str, object]] = {
        "TECHNICAL_REVIEW": TechnicalReviewHandler(),
        "COPY_EDITING": CopyEditingHandler(),
        "PEER_REVIEW": PeerReviewHandler(),
        "PUBLISHED": PublishedHandler(),
        "REJECTED": RejectedHandler(),
    }

    def patch(self, request, abstract__pid):
        article = get_object_or_404(Article, abstract__pid=abstract__pid)
        new_status = request.data.get("status")

        handler = self.STATUS_HANDLERS.get(new_status)
        if handler:
            return handler.handle(article, request)
        return Response({"error": "Invalid status"}, status=400)
