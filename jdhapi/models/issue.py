from django.db import models
from django.conf import settings
from django.utils import timezone


class Issue(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    pid = models.CharField(max_length=10, unique=True, default="jdh001")
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    creation_date = models.DateTimeField(default=timezone.now)
    publication_date = models.DateTimeField(blank=True, null=True)
    data = models.JSONField(verbose_name=u'data contents', help_text='JSON format', default=dict, blank=True)

    def __str__(self):
        return self.name
