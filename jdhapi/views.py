from jdhapi.models.role import Role
import logging
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
from jdhapi.serializers.abstract import AbstractSerializer
from jdhapi.serializers.abstract import AbstractSlimSerializer
from jdhapi.serializers.author import AuthorSlimSerializer
from jdhapi.serializers.role import RoleSerializer
from jdhapi.serializers.dataset import DatasetSlimSerializer
from jdhapi.serializers.article import ArticleSerializer
from jdhapi.serializers.issue import IssueSerializer
from jdhapi.serializers.tag import TagSerializer
from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.decorators import authentication_classes
from rest_framework import filters
from drf_recaptcha.fields import ReCaptchaV2Field
from rest_framework.serializers import Serializer
from django.core.mail import send_mail
from jdh.validation import JSONSchema
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from django.http import Http404


document_json_schema = JSONSchema(filepath='submit-abstract.json')
logger = logging.getLogger(__name__)


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


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'authors': reverse('author-list', request=request, format=format),
        'datasets': reverse('dataset-list', request=request, format=format),
        'abstracts': reverse('abstract-list', request=request, format=format),
        'articles': reverse('article-list', request=request, format=format),
        'issues': reverse('issue-list', request=request, format=format),
        'tags': reverse('tag-list', request=request, format=format),
    })


@api_view(['GET'])
def GenerateNotebook(request, pid):
    abstractsubmission = get_object_or_404(Abstract, pid=pid)
    return Response({
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {
            "jdh": {
                "pid": abstractsubmission.pid
            }
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "jdh": {
                        "section": "title"
                    }
                },
                "source": abstractsubmission.title.split('\n')
            }
        ]
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def SubmitAbstract(request):
    try:
        document_json_schema.validate(instance=request.data)
    except ValidationError as err:
        logger.exception(err)
        return Response({
            'error': 'ValidationError',
            'message': err.message
        }, status=status.HTTP_400_BAD_REQUEST)
    except SchemaError as err:
        logger.exception(err)
        return Response({
            'error': 'SchemaError',
            'message': err.message
        }, status=status.HTTP_400_BAD_REQUEST)
    logger.info('submit abstract validated.')
    contact = request.data.get("contact")
    if(request.data.get("callForPapers")):
        logger.info(f'call of paper {request.data.get("callForPapers")}')
        try:
            call_paper = CallOfPaper.objects.get(
                folder_name=request.data.get("callForPapers"))
            abstract = Abstract(
                title=request.data.get("title"),
                abstract=request.data.get("abstract"),
                contact_orcid=contact.get("orcid", ""),
                contact_affiliation=contact.get("affiliation"),
                contact_email=contact.get("email"),
                contact_lastname=contact.get("lastname"),
                contact_firstname=contact.get("firstname"),
                consented=request.data.get("acceptConditions"),
                callpaper=call_paper
            )
        except CallOfPaper.DoesNotExist:
            raise Http404("Call of paper does not exist")
    else:
        abstract = Abstract(
            title=request.data.get("title"),
            abstract=request.data.get("abstract"),
            contact_orcid=contact.get("orcid", ""),
            contact_affiliation=contact.get("affiliation"),
            contact_email=contact.get("email"),
            contact_lastname=contact.get("lastname"),
            contact_firstname=contact.get("firstname"),
            consented=request.data.get("acceptConditions")
        )
    abstract.save()
    authors = request.data.get('authors', [])
    for author in authors:
        new_author = Author(
            lastname=author['lastname'],
            firstname=author['firstname'],
            email=author.get('email', ''),
            affiliation=author['affiliation'],
            orcid=author.get('orcid', '')
        )
        new_author.save()
        abstract.authors.add(new_author)
    datasets = request.data.get('datasets', [])
    for dataset in datasets:
        new_dataset = Dataset(
            url=dataset['url'],
            description=dataset['description']
        )
        new_dataset.save()
        abstract.datasets.add(new_dataset)
    logger.info("End submit abstract")
    # Send an email of confirmation
    sendmailAbstractReceived(abstract.title, abstract.contact_email, abstract.contact_firstname, abstract.contact_lastname)
    serializer = AbstractSerializer(abstract)
    return Response(serializer.data)


class V2Serializer(Serializer):
    token = ReCaptchaV2Field()


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'lastname', 'firstname', 'affiliation', 'orcid']
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
    filterset_fields = ['id', 'url', 'description']


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
    filterset_fields = ["id", "pid", "title", "abstract", "callpaper", "submitted_date", "validation_date", "contact_orcid", "contact_affiliation", "contact_lastname", "contact_firstname", "status", "consented", "authors"]

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.serializer_class = CreateAbstractSerializer
        super().create(request, *args, **kwargs)
        return Response({'received data': request.data})


class AbstractDetail(generics.RetrieveUpdateDestroyAPIView):
    # TO UPDATE OR DELETE need to be authenticated
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Abstract.objects.all()
    serializer_class = AbstractSlimSerializer
    lookup_field = "pid"


class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["issue", "abstract", "status", "tags", "authors", "copyright_type"]
    ordering_fields = ["issue__publication_date", "publication_date"]
    ordering = ["-issue__publication_date", "-publication_date"]

    def get_queryset(self):
        """
        Optionally restricts the returned articles to a given issue,
        by filtering against a `pid` query parameter in the URL.
        """
        queryset = Article.objects.all()
        pid = self.request.query_params.get('pid')
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
    filterset_fields = ["id", "pid", "name", "description", "creation_date", "publication_date", "cover_date", "status", "volume", "issue"]
    ordering_fields = ["creation_date", "publication_date"]


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
