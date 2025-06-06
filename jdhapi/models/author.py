from django.db import models
from django_countries.fields import CountryField


class Author(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    email = models.EmailField(max_length=254, null=True, blank=True)
    lastname = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50)
    orcid = models.CharField(max_length=50, null=True, blank=True)
    affiliation = models.CharField(max_length=250)
    github_id = models.CharField(max_length=39, null=True, blank=True)
    bluesky_id = models.CharField(max_length=255, null=True, blank=True)
    facebook_id = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(blank=True, null=True)

    class Meta:
        ordering = ["lastname"]

    def __str__(self):
        return self.lastname
