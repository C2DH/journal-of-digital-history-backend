from rest_framework import serializers
from jdhapi.models import Abstract


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
            "contact_orcid",
            "contact_affiliation",
            "contact_lastname",
            "contact_firstname",
            "language_preference",
            "status",
            "consented",
            "authors",
            "datasets",
        )
        extra_kwargs = {
            "authors": {"required": False},
            "datasets": {"required": False},
        }
