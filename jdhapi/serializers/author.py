from typing import ClassVar

from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from ..models.abstract import Abstract
from ..models.author import Author


class CountrySerializer(serializers.Serializer):
    country = CountryField()


class AuthorAbstractsSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    abstracts = serializers.SerializerMethodField()
    accepted = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    def get_country(self, obj):
        return str(obj.country)

    def get_abstracts(self, obj):
        return Abstract.objects.filter(authors__id=obj.id).count()

    def get_accepted(self, obj):
        author_abstracts = Abstract.objects.filter(authors__id=obj.id)
        return author_abstracts.filter(status="ACCEPTED").count()
    
    def get_published(self, obj):
        author_abstracts = Abstract.objects.filter(authors__id=obj.id)
        return author_abstracts.filter(status="PUBLISHED").count()

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
            "abstracts",
            "accepted",
            "published"
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
