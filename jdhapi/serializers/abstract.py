from jdhapi.models import Abstract, Article
from rest_framework import serializers


class CreateAbstractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abstract
        fields = "__all__"

    def validate(self, data):
        print("@validate", data)
        # validate against a JSON SCHEMA on
        return data


class AbstractSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    datasets = serializers.SerializerMethodField()

    class Meta:
        model = Abstract
        fields = (
            "id",
            "pid",
            "title",
            "abstract",
            "callpaper",
            "submitted_date",
            "validation_date",
            "language_preference",
            "contact_affiliation",
            "contact_email",
            "contact_lastname",
            "contact_firstname",
            "status",
            "consented",
            "authors",
            "datasets",
        )
        extra_kwargs = {
            "authors": {"required": False},
            "datasets": {"required": False},
        }

    def get_authors(self, obj):
        from jdhapi.serializers.author import AuthorSlimSerializer

        return AuthorSlimSerializer(obj.authors.all().order_by("id"), many=True).data

    def get_datasets(self, obj):
        from jdhapi.serializers.dataset import DatasetSlimSerializer

        return DatasetSlimSerializer(obj.datasets.all(), many=True).data

    def create(self, validated_data):
        abstract = Abstract(**validated_data)
        return abstract


class AbstractSlimSerializer(serializers.ModelSerializer):
    callpaper_title = serializers.SerializerMethodField()
    repository_url = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    issue = serializers.SerializerMethodField()

    class Meta:
        model = Abstract
        fields = (
            "id",
            "pid",
            "title",
            "abstract",
            "callpaper",
            "callpaper_title",
            "submitted_date",
            "validation_date",
            "contact_affiliation",
            "contact_lastname",
            "contact_email",
            "contact_firstname",
            "language_preference",
            "status",
            "consented",
            "authors",
            "datasets",
            "issue",
            "repository_url",
        )
        extra_kwargs = {
            "authors": {"required": False},
            "datasets": {"required": False},
        }

    def get_callpaper_title(self, obj):
        if obj.callpaper:
            return obj.callpaper.title
        return None

    def get_repository_url(self, obj):
        # Access the related Article object via the reverse relation
        article = getattr(obj, "article", None)
        if article and article.repository_url:
            return article.repository_url
        return None

    def get_contact_email(self, obj):
        # Try to find an author matching the contact's first and last name
        contact_lastname = getattr(obj, "contact_lastname", None)
        contact_firstname = getattr(obj, "contact_firstname", None)

        if contact_lastname and contact_firstname:
            author = obj.authors.filter(
                lastname=contact_lastname, firstname=contact_firstname
            ).first()
            if author and author.email:
                return author.email
            else:
                return obj.contact_email
        return None

    def get_issue(self, obj):
        article = Article.objects.filter(abstract__pid=obj.pid).first()
        if article and article.issue:
            return article.issue.id
        return None
