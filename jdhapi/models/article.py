from django.conf import settings
from django.db import models
import logging
import datetime
import marko
from django.core.exceptions import ValidationError
from . import Abstract
from weasyprint import HTML
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver
from lxml import html
from model_utils import FieldTracker

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
    tracker = FieldTracker(fields=['status'])
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
    dataverse_url = models.URLField(max_length=200, blank=True, null=True, help_text="Url to find here https://data.journalofdigitalhistory.org/")  # New field for Dataverse URL
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

    def get_kernel_language(self):
        first_tag = self.tags.first()  # Get the first tag related to the article
        if first_tag:
            return first_tag.data.get('language', '')
        return ''  # Default language if no tag or language field is present

    def __str__(self):
        return self.abstract.title

    def send_email_if_peer_review(self):
        if self.status == self.Status.PEER_REVIEW:
            # Render the PDF template
            template = 'jdhseo/peer_review.html'
            if 'title' in self.data:
                articleTitle = html.fromstring(marko.convert(self.data['title'][0])).text_content()
                context = {'article': self, 'articleTitle': articleTitle}
                html_string = render_to_string(template, context)

                # Generate the PDF
                pdf_file = HTML(string=html_string).write_pdf()
                logger.info("Pdf generated")
                filename = 'peer_review_' + self.abstract.pid + '.pdf'
                # Save the PDF to a file
                # with open(filename, 'wb') as f:
                #    f.write(pdf_file)
                # logger.info("Pdf saved")
                # Create an email message with the PDF attachment
                subject = f"{articleTitle} can been sent to peer review!"
                body = 'Please find attached the links useful for the peer review.'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = settings.DEFAULT_TO_EMAIL
                email = EmailMessage(subject, body, from_email, [to_email])
                email.attach(filename, pdf_file, 'application/pdf')

                # Send the email
                try:
                    email.send()
                    logger.info("Email sent")
                except Exception as e:
                    print(f'Error sending email: {str(e)}')