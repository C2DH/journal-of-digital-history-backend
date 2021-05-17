from rest_framework import serializers
from jdhapi.models import Abstract, Author, Dataset, Status


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    lastname = serializers.CharField(max_length=50)
    firstname = serializers.CharField(max_length=50)
    affiliation = serializers.CharField(max_length=250)
    email = serializers.EmailField(required=False, allow_blank=True, max_length = 254)
    orcid = serializers.CharField(required=False, allow_blank=True,max_length=50)

    def create(self, validated_data):
        print("inside create serializer")
        """
        Create and return a new `Author` instance, given the validated data.
        """
        return Author.objects.create(**validated_data)

    def update(self, instance, validated_data):
        print("inside update serializer")
        """
        Update and return an existing `Author` instance, given the validated data.
        """
        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.firstname = validated_data.get('firstname', instance.firstname)
        instance.affiliation = validated_data.get('affiliation', instance.affiliation)
        instance.email = validated_data.get('email', instance.email)
        instance.orcid = validated_data.get('orcid', instance.orcid)
        instance.save()
        return instance

class DatasetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.URLField(required=False, allow_blank=True,max_length = 254)
    description = serializers.CharField(required=False, allow_blank=True, style={'base_template':'textarea.html'})



    def create(self, validated_data):
        """
        Create and return a new `Dataset` instance, given the validated data.
        """
        return Dataset.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Dataset` instance, given the validated data.
        """
        instance.url = validated_data.get('url', instance.url)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

class AbstractSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=250)
    abstract = serializers.CharField(style={'base_template':'textarea.html'})
   # contact_lastname = serializers.CharField(max_length=50)
   # contact_firstname = serializers.CharField(max_length=50)
   # contact_affiliation = serializers.CharField(max_length=250)
   # contact_email = serializers.EmailField(max_length = 254)
   # contact_orcid = serializers.CharField(required=False, allow_blank=True,max_length=50)
   # consented = serializers.BooleanField()
    status = serializers.ChoiceField(
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    authors = AuthorSerializer(many=True, read_only=False, required=False)
    datasets = DatasetSerializer(many=True, read_only=False, required=False)
    


    def create(self, validated_data):
        """
        Create and return a new `Abstract` instance, given the validated data.
        """
        return Abstract.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Abstract` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.abstract = validated_data.get('abstract', instance.abstract)
        instance.contact_lastname = validated_data.get('contact_lastname', instance.contact_lastname)
        instance.contact_firstname = validated_data.get('contact_firstname', instance.contact_firstname)
        instance.contact_affiliation = validated_data.get('contact_affiliation', instance.contact_affiliation)
        instance.contact_email = validated_data.get('contact_email', instance.contact_email)
        instance.contact_orcid = validated_data.get('contact_orcid', instance.contact_orcid)
        instance.consented = validated_data.get('consented', instance.consented)
        instance.status = validated_data.get('status', instance.status)
        instance.authors = validated_data.get('authors', instance.authors)
        instance.datasets = validated_data.get('datasets', instance.datasets)
        instance.save()
        return instance
