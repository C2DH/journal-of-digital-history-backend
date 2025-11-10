from django_filters.rest_framework import DjangoFilterBackend
from jdhapi.models import Article
from jdhapi.serializers.article import ArticleSerializer
from rest_framework import generics, filters


class AdvanceArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [
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
         return Article.objects.filter(issue__status='DRAFT', status='PUBLISHED')

    