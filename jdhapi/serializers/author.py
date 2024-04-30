from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import serializers
from ..models.author import Author
from django_countries.serializer_fields import CountryField


class CountrySerializer(serializers.Serializer):
    country = CountryField()

class AuthorSerializer(serializers.ModelSerializer):
    abstracts = AbstractSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ['id', 'lastname', 'firstname', 'affiliation', 'email', 'orcid', 'abstracts']


class AuthorSlimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ['id', 'lastname', 'firstname', 'affiliation', 'orcid','city','country']
