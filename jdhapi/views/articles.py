from jdhapi.models import Article
from jdhapi.serializers.article import ArticleSerializer
from rest_framework import generics, filters
from rest_framework.permissions import BasePermission


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
    ]
    ordering_fields = [
        "issue__publication_date",
        "publication_date",
        "abstract__title",
        "abstract__pid",
    ]
    ordering = ["-issue__publication_date", "-publication_date"]
    search_fields = ["abstract__title"]

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
        # applying SearchFilter on title
        qs = super().filter_queryset(queryset)

        # if ?search= was provided, also including exact‐pid matches
        term = self.request.query_params.get("search")
        if term:
            qs = super().filter_queryset(queryset)
            pid_qs = queryset.filter(abstract__pid__iexact=term)
            qs = (qs | pid_qs).distinct()

        return qs


class ArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedForNonPublished]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = "abstract__pid"
