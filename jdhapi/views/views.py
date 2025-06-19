from datetime import date
from jdhapi.models.role import Role
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from jdhapi.models import Abstract
from jdhapi.models import Author
from jdhapi.models import Dataset
from jdhapi.models import Article
from jdhapi.models import Issue
from jdhapi.models import Tag
from jdhapi.models import CallOfPaper
from jdhapi.serializers.abstract import CreateAbstractSerializer
from jdhapi.serializers.abstract import AbstractSlimSerializer
from jdhapi.serializers.author import AuthorSlimSerializer
from jdhapi.serializers.role import RoleSerializer
from jdhapi.serializers.dataset import DatasetSlimSerializer
from jdhapi.serializers.article import ArticleSerializer
from jdhapi.serializers.issue import IssueSerializer
from jdhapi.serializers.tag import TagSerializer
from jdhapi.serializers.callofpaper import CallOfPaperSerializer
from rest_framework import permissions
from rest_framework.response import Response
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework.serializers import Serializer


class V2Serializer(Serializer):
    token = ReCaptchaV2Field()


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "lastname", "firstname", "affiliation", "orcid"]
    # filter_backends = [filters.SearchFilter]
    # search_fields = ['lastname']


class AuthorDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer


class DatasetList(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSlimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "url", "description"]


class DatasetDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Dataset.objects.all()
    serializer_class = DatasetSlimSerializer


class AbstractList(generics.ListCreateAPIView):
    queryset = Abstract.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AbstractSlimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "id",
        "pid",
        "title",
        "abstract",
        "callpaper",
        "submitted_date",
        "validation_date",
        "language_preference",
        "contact_affiliation",
        "contact_lastname",
        "contact_firstname",
        "status",
        "consented",
        "authors",
    ]

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.serializer_class = CreateAbstractSerializer
        super().create(request, *args, **kwargs)
        return Response({"received data": request.data})


class AbstractDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Abstract.objects.all()
    serializer_class = AbstractSlimSerializer
    lookup_field = "pid"


class IsOwnerFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_staff:
            return queryset  # Staff members can see all articles
        else:
            return queryset.filter(status=Article.Status.PUBLISHED)


class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [IsOwnerFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        "issue",
        "abstract",
        "status",
        "tags",
        "authors",
        "copyright_type",
    ]
    ordering_fields = ["issue__publication_date", "publication_date"]
    ordering = ["-issue__publication_date", "-publication_date"]

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


class ArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = "abstract__pid"


class IssueList(generics.ListCreateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        "id",
        "pid",
        "name",
        "description",
        "creation_date",
        "publication_date",
        "cover_date",
        "status",
        "volume",
        "issue",
        "is_open_ended",
    ]
    ordering_fields = ["creation_date", "publication_date", "pid"]


class IssueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    lookup_field = "pid"


class RoleList(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "order_id", "author", "article"]


class RoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Issue.objects.all()
    serializer_class = RoleSerializer


class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "category", "name"]


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CallOfPaperList(generics.ListCreateAPIView):
    queryset = CallOfPaper.objects.filter(deadline_abstract__gte=date.today())
    serializer_class = CallOfPaperSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "id",
        "deadline_abstract",
        "deadline_article",
        "title",
        "folder_name",
    ]


class CallOfPaperDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CallOfPaper.objects.all()
    serializer_class = CallOfPaperSerializer
    ordering_fields = ["deadline_abstract", "deadline_article"]
    lookup_field = "folder_name"
