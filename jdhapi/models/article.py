from django.db import models


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
    # Url of the article in the front
    notebook_url = models.CharField(max_length=254, null=True, blank=True)
    # Json source from raw.github
    notebook_ipython_url = models.URLField(max_length=254, null=True, blank=True)
    notebook_commit_hash = models.CharField(
        max_length=22, default='', help_text='store the git hash', blank=True)
    notebook_path = models.CharField(max_length=254, null=True, blank=True)
    binder_url = models.URLField(max_length=254, null=True, blank=True)
    doi = models.CharField(max_length=254, null=True, blank=True)
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
    data = models.JSONField(
        verbose_name=u'data contents', help_text='JSON format',
        default=dict, blank=True)
    fingerprint = models.JSONField(
        verbose_name=u'fingerprint contents', help_text='JSON format',
        default=dict, blank=True)
    citation = models.JSONField(
        verbose_name=u'citation contents', help_text='JSON format',
        default=dict, blank=True)
    tags = models.ManyToManyField('jdhapi.Tag', blank=True)
    authors = models.ManyToManyField('jdhapi.Author', through='Role')

    def __str__(self):
        return self.abstract.title


