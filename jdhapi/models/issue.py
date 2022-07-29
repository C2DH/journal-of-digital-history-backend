from django.db import models
from django.conf import settings
from django.utils import timezone


class Issue(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft',
        PUBLISHED = 'PUBLISHED', 'Published'

    id = models.AutoField(primary_key=True, db_column="id")
    pid = models.CharField(max_length=10, unique=True, default="jdh001")
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    creation_date = models.DateTimeField(default=timezone.now)
    publication_date = models.DateTimeField(blank=True, null=True)
    data = models.JSONField(verbose_name=u'data contents', help_text='JSON format', default=dict, blank=True)
    # YEAR OF PUBLICATION
    # 2021  - volume 1
    # 2022 -  volume 2
    volume = models.PositiveSmallIntegerField(null=True)
    # ISSUE
    # first issue - issue 1
    issue = models.PositiveSmallIntegerField(null=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    def __str__(self):
        return self.pid
