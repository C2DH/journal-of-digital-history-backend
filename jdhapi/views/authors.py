from rest_framework import generics, filters
from jdhapi.models import Author
from jdhapi.serializers.author import AuthorSlimSerializer
from django_filters.rest_framework import DjangoFilterBackend


class AuthorList(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSlimSerializer
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
