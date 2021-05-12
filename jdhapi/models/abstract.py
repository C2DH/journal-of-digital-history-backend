from django.db import models
from django.conf import settings
from django.utils import timezone
import shortuuid




def create_short_url():
    return shortuuid.uuid()[:12]  # es => "IRVaY2b3VI89"

class Abstract(models.Model):

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted',
        ACCEPTED = 'ACCEPTED', 'Accepted',
        DECLINED = 'DECLINED', 'Declined'


    id= models.AutoField(primary_key=True, db_column="id")
    pid = models.CharField(max_length=255,default=create_short_url, db_index=True)
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
    authors = models.ManyToManyField('jdhapi.Author', related_name='abstracts', blank=True)
    datasets = models.ManyToManyField('jdhapi.Dataset', related_name='abstracts',blank=True)
    consented = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)

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

