from django.db import models
from django.conf import settings
from django.utils import timezone
import shortuuid


class Dataset(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    url = models.URLField(max_length=254, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
