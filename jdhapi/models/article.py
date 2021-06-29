from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField
import shortuuid


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft',
        INTERNAL_REVIEW = 'INTERNAL_REVIEW', 'Internal_review',
        EXTERNAL_REVIEW = 'EXTERNAL_REVIEW', 'External_review',
        PUBLISHED = 'PUBLISHED', 'Published'

    class RepositoryType(models.TextChoices):
        GITHUB = 'GITHUB', 'Github',
        GITLAB = 'GITLAB', 'Gitlab',

    abstract = models.OneToOneField(
        'jdhapi.Abstract',
        on_delete=models.CASCADE,
        primary_key=True,
    )

    repository_url = models.URLField(max_length=254, null=True, blank=True)
    notebook_url = models.CharField(max_length=254, null=True, blank=True)
    notebook_commit_hash = models.CharField(max_length=22, default='', help_text='store the git hash', blank=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    repository_type = models.CharField(
        max_length=15,
        choices=RepositoryType.choices,
        default=RepositoryType.GITHUB,
    )
    issue = models.ForeignKey('jdhapi.Issue', on_delete=models.CASCADE)
    data = models.JSONField(verbose_name=u'data contents', help_text='JSON format', default=dict, blank=True)
    tags = models.ManyToManyField('jdhapi.Tag', blank=True)
    authors = models.ManyToManyField('jdhapi.Author', through='Role')

    def __str__(self):
        return self.abstract.title
