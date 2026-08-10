from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from jdhapi.models import Author
from jdhapi.serializers.author import AuthorAbstractsSerializer, AuthorSlimSerializer


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorAbstractsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["id", "lastname", "firstname", "affiliation", "orcid"]
    ordering_fields = [
        "id",
        "lastname",
        "firstname",
        "affiliation",
    ]


class AuthorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer
