from typing import ClassVar

from django.db.models import Value
from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from ..models import Abstract, Article, Author


class CountrySerializer(serializers.Serializer):
    country = CountryField()


class AuthorSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    abstracts = serializers.SerializerMethodField()
    accepted = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    contributions = serializers.SerializerMethodField()

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

    def get_contributions(self, obj):
        abstracts = (
            Abstract.objects.filter(authors__id=obj.id, article__isnull=True)
            .annotate(type=Value("abstracts"))
            .values("pid", "title", "status", "type")
        )
        articles = (
            Article.objects.filter(abstract__authors__id=obj.id)
            .annotate(type=Value("articles"))
            .values("abstract__pid", "abstract__title", "status", "type")
        )

        symmetric_difference = abstracts.union(articles)

        return symmetric_difference

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
            "published",
            "contributions",
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
