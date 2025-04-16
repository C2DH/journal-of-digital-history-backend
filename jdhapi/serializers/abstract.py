from rest_framework import serializers
from jdhapi.models import Abstract, Author, Dataset


class CreateAbstractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abstract
        fields = "__all__"

    def validate(self, data):
        print('@validate', data)
        # validate against a JSON SCHEMA on
        return data


class AbstractSerializer(serializers.ModelSerializer):

    class Meta:
        model = Abstract
        fields = ("id", "pid", "title", "abstract", "callpaper", "submitted_date", "validation_date", "language_preference", "contact_affiliation", "contact_email", "contact_lastname", "contact_firstname", "status", "consented", "authors", "datasets")
        extra_kwargs = {'authors': {'required': False}, 'datasets': {'required': False}}

    def create(self, validated_data):
        abstract = Abstract(**validated_data)
        return abstract


class AbstractSlimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Abstract
        fields = ("id", "pid", "title", "abstract", "callpaper", "submitted_date", "validation_date", "contact_orcid", "contact_affiliation", "contact_lastname", "contact_firstname", "status", "consented", "authors", "datasets")
        extra_kwargs = {'authors': {'required': False}, 'datasets': {'required': False}}
