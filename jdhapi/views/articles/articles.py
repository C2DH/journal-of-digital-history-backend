from jdhapi.models import Article
from jdhapi.serializers.article import ArticleSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from jdhapi.views.articles.status_handlers import TechnicalReviewHandler
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

class IsOwnerFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_staff:
            return queryset  # Staff members can see all articles
        else:
            return queryset.filter(status=Article.Status.PUBLISHED)


class IsAuthenticatedForNonPublished(BasePermission):
    """
    Custom permission to allow only authenticated users to access non-published articles.
    """

    def has_object_permission(self, request, view, obj):
        if obj.status == Article.Status.PUBLISHED:
            return True
        return request.user.is_authenticated


class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [
        IsOwnerFilterBackend,
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "issue",
        "abstract",
        "status",
        "tags",
        "authors",
        "copyright_type",
        "abstract__callpaper",
    ]
    ordering_fields = [
        "issue__publication_date",
        "publication_date",
        "abstract__title",
        "abstract__pid",
    ]
    ordering = ["-issue__publication_date", "-publication_date"]
    search_fields = [
        "abstract__title",
        "abstract__pid",
        "abstract__contact_lastname",
        "abstract__contact_firstname",
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
    permission_classes = [IsAuthenticatedForNonPublished]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = "abstract__pid"



class ArticleStatus(APIView):
    permission_classes = [IsAdminUser]
    STATUS_HANDLERS = {
        'TECHNICAL_REVIEW': TechnicalReviewHandler(),
    }
    
    def patch(self, request, abstract__pid):
        article = get_object_or_404(Article, abstract__pid=abstract__pid)
        new_status = request.data.get('status')
        
        handler = self.STATUS_HANDLERS.get(new_status)
        if handler:
            return handler.handle(article, request)
        return Response({"error": "Invalid status"}, status=400)