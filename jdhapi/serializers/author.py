from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import serializers
from ..models.author import Author
from django_countries.serializer_fields import CountryField


class CountrySerializer(serializers.Serializer):
    country = CountryField()


class AuthorAbstractsSerializer(serializers.ModelSerializer):
    abstracts = AbstractSerializer(many=True, read_only=True)

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
            "abstracts",
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
        ]
