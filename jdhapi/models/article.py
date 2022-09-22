from django.db import models
import logging
import datetime
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft',
        TECHNICAL_REVIEW = 'TECHNICAL_REVIEW', 'Technical review',
        PEER_REVIEW = 'PEER_REVIEW', 'Peer review',
        DESIGN_REVIEW = 'DESIGN_REVIEW', 'Design review',
        PUBLISHED = 'PUBLISHED', 'Published'

    class CopyrightType(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft',
        CC_BY = 'CC_BY', 'CC-BY',
        CC_BY_NC_ND = 'CC_BY_NC_ND', 'CC-BY-NC-ND'

    class RepositoryType(models.TextChoices):
        GITHUB = 'GITHUB', 'Github',
        GITLAB = 'GITLAB', 'Gitlab',

    abstract = models.OneToOneField(
        'jdhapi.Abstract',
        on_delete=models.CASCADE,
        primary_key=True,
    )
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    issue = models.ForeignKey('jdhapi.Issue', on_delete=models.CASCADE)
    repository_url = models.URLField(max_length=254, null=True, blank=True, help_text="GitHub's repository URL ")
    repository_type = models.CharField(
        max_length=15,
        choices=RepositoryType.choices,
        default=RepositoryType.GITHUB,
    )
    # Url of the article in the front
    notebook_url = models.CharField(max_length=254, null=True, blank=True, help_text="Article's preview URL - All the caracters after the url : https://journalofdigitalhistory.org/en/notebook-viewer/")
    # Json source from raw.github
    notebook_ipython_url = models.URLField(max_length=254, null=True, blank=True, help_text="Raw GitHub ipynb URL")
    notebook_commit_hash = models.CharField(
        max_length=22, default='', help_text='store the git hash', blank=True)
    notebook_path = models.CharField(max_length=254, null=True, blank=True, help_text="Notebook file name with .ipynb")
    binder_url = models.URLField(max_length=254, null=True, blank=True)
    doi = models.CharField(max_length=254, null=True, blank=True, help_text="Doi received from ScholarOne -  10.1515/JDH.YYYY.XXXX.RX")
    publication_date = models.DateTimeField(blank=True, null=True)
    copyright_type = models.CharField(
        max_length=15,
        choices=CopyrightType.choices,
        default=CopyrightType.DRAFT,
    )
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

    def save(self, *args, **kwargs):
        # IF PUBLISHED
        if self.status == Article.Status.PUBLISHED:
            logger.info("Want to be published status")
            # Check mandatory fields doi
            # Set up the publication date
            self.publication_date = datetime.datetime.now()
            if self.doi:
                super(Article, self).save(*args, **kwargs)
            else:
                raise ValidationError("For publishing provide a DOI value")
        else:
            logger.info(f"status not published but status {self.status }")
            super(Article, self).save(*args, **kwargs)



