from rest_framework import serializers
from jdhapi.models import Abstract, Author, Dataset, Status


class AbstractSerializer(serializers.ModelSerializer):

    class Meta:
        model = Abstract
        fields = ("id", "title","abstract","validation_date","contact_orcid","contact_affiliation","contact_email","contact_lastname","contact_firstname","status","consented")
        #extra_kwargs = {'authors':{'required': False}, 'datasets':{'required': False}}

    def create(self, validated_data):
        print(validated_data)
        abstract = Abstract(**validated_data)
        return abstract

class AuthorSerializer(serializers.ModelSerializer):
    abstracts = AbstractSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'lastname', 'firstname', 'affiliation','email','orcid','abstracts']


class DatasetSerializer(serializers.ModelSerializer):
    abstracts = AbstractSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['id', 'url', 'description','abstracts']







