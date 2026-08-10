from typing import ClassVar

from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from ..models.abstract import Abstract
from ..models.author import Author


class CountrySerializer(serializers.Serializer):
    country = CountryField()


class AuthorAbstractsSerializer(serializers.ModelSerializer):
    abstracts = serializers.SerializerMethodField()

    def get_abstracts(self, obj):
        return Abstract.objects.filter(authors__id=obj.id).count()

    class Meta:
        model = Author
        fields: ClassVar[list[str]] = [
            "id",
            "lastname",
            "firstname",
            "affiliation",
            "email",
            "orcid",
            "github_id",
            "bluesky_id",
            "facebook_id",
            "linkedin_id",
            "abstracts",
        ]


class AuthorSlimSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    def get_country(self, obj):
        return str(obj.country)

    class Meta:
        model = Author
        fields: ClassVar[list[str]] = [
            "id",
            "lastname",
            "firstname",
            "affiliation",
            "email",
            "orcid",
            "city",
            "country",
            "github_id",
            "bluesky_id",
            "facebook_id",
            "linkedin_id",
        ]
