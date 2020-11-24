from django.db import models
from django.conf import settings
from django.utils import timezone




""" TODO:rename class and parameter according to json daniele """
# Create your models here.
class Status(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted',
    ACCEPTED = 'ACCEPTED', 'Accepted',
    DECLINED = 'DECLINED', 'Declined'


class Contributor(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    email = models.EmailField(max_length = 254, null=True, blank=True)
    lastname = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50)
    orcid = models.CharField(max_length=50,null=True, blank=True)
    institution = models.CharField(max_length=250)

    class Meta:
        ordering = ['lastname']

    def __str__(self):
        return self.lastname

class Ressource(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    url = models.URLField(max_length = 254,null=True, blank=True)
    description = models.TextField(null=True, blank=True)



class AbstractSubmission(models.Model):
    id= models.AutoField(primary_key=True, db_column="id")
    title = models.CharField(max_length=250)
    abstract = models.TextField()
    submitted_date = models.DateTimeField(default=timezone.now)
    validation_date = models.DateTimeField(blank=True, null=True)
    submitter_orcid = models.CharField(max_length=50)
    submitter_institution = models.CharField(max_length=250)
    submitter_email = models.EmailField(max_length = 254)
    submitter_lastname = models.CharField(max_length=50)
    submitter_firstname = models.CharField(max_length=50)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    contributors = models.ManyToManyField(Contributor)
    ressources = models.ManyToManyField(Ressource)
    consented = models.BooleanField(default=False)

    class Meta:
        ordering = ['title']

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

