import marko
from django import forms
from jdhapi.models import Article, article, Abstract
from jdhapi.utils.gitup_repository import is_socialmediacover_exist
import logging
import datetime
from django.http import Http404
from django.utils import timezone
import weasyprint
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from lxml import html

logger = logging.getLogger(__name__)


class ArticleForm(forms.ModelForm):

    abstract = forms.ModelChoiceField(
        queryset=Abstract.objects.filter(article__isnull=True).order_by('title'),
        label='Abstract',
        disabled=True
    )

    class Meta:
        model = Article
        fields = '__all__'

    def clean(self):
        # Get the article data
        article = self.instance
        doi = self.cleaned_data['doi']
        status = self.cleaned_data['status']
        repository_url = self.cleaned_data['repository_url']
        notebook_url = self.cleaned_data['notebook_url']
        notebook_path = self.cleaned_data['notebook_path']
        binder_url = self.cleaned_data['binder_url']
        notebook_ipython_url = self.cleaned_data['notebook_ipython_url']
        if self.has_changed():
            logger.info("The following fields changed: %s" % ", ".join(self.changed_data))
            if 'status' in self.changed_data:
                # IF PUBLISHED
                if status == Article.Status.PUBLISHED:
                    if not doi:
                        raise forms.ValidationError({'doi': "Doi is mandatory if published"})
                    if not is_socialmediacover_exist(repository_url):
                        raise forms.ValidationError({'repository_url': "No social media cover uploaded in the GitHub repository"})
                    else:
                        self.cleaned_data['publication_date'] = datetime.datetime.now()
                        logger.info(f"primary key {self.instance.pk}")
                        try:
                            abstract = Abstract.objects.get(id=self.instance.pk)
                            abstract.status = Abstract.Status.PUBLISHED
                            # This prevents triggering any signals that you may not want to invoke.
                            abstract.save(update_fields=['status'])
                        except Article.DoesNotExist:
                            # do something in case not
                            logger.error("No abstract found")
                            # Abstract.objects.filter(pid=self.instance.pk).update(status=Abstract.Status.PUBLISHED)
                            raise Http404("Abstract linked to the article does not exist")
            if status == Article.Status.PEER_REVIEW:
                if not repository_url:
                    raise forms.ValidationError({'repository_url': "Repository_url is mandatory if published"})
                if not notebook_url:
                    raise forms.ValidationError({'notebook_url': "Notebook_url is mandatory if published"})
                if not notebook_path:
                    raise forms.ValidationError({'notebook_path': "Notebook_url is mandatory if published"})
                # Render the PDF template
                template = 'jdhseo/peer_review.html'
                if 'title' in article.data:
                    articleTitle = html.fromstring(marko.convert(article.data['title'][0])).text_content()
                context = {'article': article, 'articleTitle': articleTitle}
                html_string = render_to_string(template, context)

                # Generate the PDF
                pdf_file = weasyprint.HTML(string=html_string).write_pdf()
                logger.info("Pdf generated")
                filename = 'peer_review_' + article.abstract.pid + '.pdf'
                # Save the PDF to a file
                with open(filename, 'wb') as f:
                    f.write(pdf_file)
                logger.info("Pdf saved")
                # Create an email message with the PDF attachment
                subject = 'Peer review PDF ' + articleTitle
                body = 'Please find attached the peer review PDF for your article.'
                from_email = 'jdh.admin@uni.lu'
                to_email = 'eliselavy@gmail.com'
                email = EmailMessage(subject, body, from_email, [to_email])
                email.attach(filename, pdf_file, 'application/pdf')

                # Send the email
                email.send()
                logger.info("Email sent")
        else:
            logger.info("no changed fields")

