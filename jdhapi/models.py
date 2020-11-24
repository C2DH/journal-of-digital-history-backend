from django.db import models
from django.conf import settings
from django.utils import timezone




""" TODO:rename class and parameter according to json daniele """
# Create your models here.
class Status(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted',
    ACCEPTED = 'ACCEPTED', 'Accepted',
    DECLINED = 'DECLINED', 'Declined'


class Author(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    email = models.EmailField(max_length = 254, null=True, blank=True)
    lastname = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50)
    orcid = models.CharField(max_length=50,null=True, blank=True)
    affiliation = models.CharField(max_length=250)

    class Meta:
        ordering = ['lastname']

    def __str__(self):
        return self.lastname

class Dataset(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    url = models.URLField(max_length = 254,null=True, blank=True)
    description = models.TextField(null=True, blank=True)



class Abstract(models.Model):
    id= models.AutoField(primary_key=True, db_column="id")
    title = models.CharField(max_length=250)
    abstract = models.TextField()
    submitted_date = models.DateTimeField(default=timezone.now)
    validation_date = models.DateTimeField(blank=True, null=True)
    contact_orcid = models.CharField(max_length=50)
    contact_affiliation = models.CharField(max_length=250)
    contact_email = models.EmailField(max_length = 254)
    contact_lastname = models.CharField(max_length=50)
    contact_firstname = models.CharField(max_length=50)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    authors = models.ManyToManyField(Author, related_name='abstracts', blank=True)
    datasets = models.ManyToManyField(Dataset, related_name='abstracts',blank=True)
    consented = models.BooleanField(default=False)

    class Meta:
        ordering = ['submitted_date']

    def accepted(self):
        self.validation_date = timezone.now()
        self.status = Status.ACCEPTED
        self.save()

    def declined(self):
        self.validation_date = timezone.now()
        self.status = Status.DECLINED
        self.save()

    def __str__(self):
        return self.title

