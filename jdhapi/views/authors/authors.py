from typing import ClassVar

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from jdhapi.models import Author
from jdhapi.serializers.author import AuthorAbstractsSerializer, AuthorSlimSerializer


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorAbstractsSerializer
    permission_classes: ClassVar[list[object]] = [permissions.IsAdminUser]
    filter_backends: ClassVar[list[object]] = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter
    ]
    filterset_fields: ClassVar[list[str]] = [
        "id",
        "lastname",
        "firstname",
        "affiliation",
        "orcid",
    ]
    ordering_fields: ClassVar[list[str]] = [
        "id",
        "lastname",
        "firstname",
        "affiliation",
    ]
    search_fields: ClassVar[list[str]] = [
        "lastname",
        "firstname",
        "affiliation",
    ]


class AuthorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer
    permission_classes: ClassVar[list[object]] = [permissions.IsAdminUser]
