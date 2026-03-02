from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from jdhapi.serializers.abstract import AbstractSlimSerializer

from ..models.author import Author


class CountrySerializer(serializers.Serializer):
    country = CountryField()


class AuthorAbstractsSerializer(serializers.ModelSerializer):
    abstracts = AbstractSlimSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = [
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
            "abstracts"
        ]


class AuthorSlimSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    def get_country(self, obj):
        return str(obj.country)

    class Meta:
        model = Author
        fields = [
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
