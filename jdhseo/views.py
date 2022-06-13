import base64
import logging
import requests
import urllib.parse
from django.http import Http404
from django.shortcuts import render
from jdhapi.models import Article, Issue, Author
from django.conf import settings
from .utils import parseJupyterNotebook, generate_qrcode, getDoiUrlDGFormatted
from .utils import getPlainMetadataFromArticle
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def ArticleDetail(request, pid):
    published_date = ""
    # get ONLY published article matching the pid
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    # generate qrcode
    qrCodebase64 = generate_qrcode(pid)
    # get doi url format for DG
    doi_url = getDoiUrlDGFormatted(article.doi)
    # Publish online
    if (article.publication_date):
        published_date = article.publication_date.date()
    # decode notebook url
    notebook_url = urllib.parse.unquote(
        base64.b64decode(article.notebook_url).decode('utf-8'))
    # contact_orcid
    ORCID_URL = "https://orcid.org/"
    contact_orcid = article.abstract.contact_orcid.partition(ORCID_URL)[2]
    # fill the context for the template file.
    context = {
        'article': article,
        'article_absolute_url':
            f"https://journalofdigitalhistory.org/en/article/"
            f"{article.abstract.pid}",
        'qr_code': qrCodebase64,
        'media_url': settings.MEDIA_URL,
        'doi_url': doi_url,
        'published_date': published_date
    }
    # check if it is a github url

    context.update({'proxy': 'github', 'host': settings.JDHSEO_PROXY_HOST})
    if notebook_url.startswith(settings.JDHSEO_PROXY_PATH_GITHUB):
        # load contents from remote link (it uses nginx cache if availeble.
        # this can be improved using local cacle mechanism
        # Cf. https://docs.djangoproject.com/en/3.2/topics/cache/
        remote_url = urllib.parse.urljoin(
            settings.JDHSEO_PROXY_HOST, notebook_url)
        try:
            res = requests.get(remote_url)
            # add NB paragraphs to context
            context.update({'nb': parseJupyterNotebook(res.json(), contact_orcid)})
        except Exception as e:
            logger.error(
                f'Error occurred on article pk={article.pk}'
                f' notebook remote_url={remote_url}')
            logger.exception(e)
            raise Http404("Article Notebook file not found (or not valid)")
    else:
        logger.error(
            f'Article(pid={pid}).notebook_url is BAD:"{notebook_url}"')
        raise Http404("Article does not exist")
    # get content from notebook_url using our proxy
    # r = requests.get('https://api.github.com/user')
    return render(request, 'jdhseo/article_detail.html', context)


def IssueDetail(request, pid):
    try:
        issue = Issue.objects.get(
            pid=pid,
            status=Issue.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Issue does not exist")

    articles = Article.objects.filter(
        issue__pid=pid,
        status=Article.Status.PUBLISHED)
    context = {
        'site_base_url': 'https://journalofdigitalhistory.org',
        'issue': issue,
        'count_articles': articles.count(),
        'plain_articles': [
            getPlainMetadataFromArticle(article=a)
            for a in articles
        ]
    }
    return render(request, 'jdhseo/issue_detail.html', context)


def ArticleXmlDG(request, pid):
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
        nbauthors = article.abstract.authors.count()
        logger.debug(f'Nb Authors(count={nbauthors}) for article {pid}')
        authors = []
        for author in article.abstract.authors.all():
            contrib = {
                "given_names": author.firstname,
                "surname": author.lastname
            }
            authors.append(contrib)
            logger.debug(f'authors {authors}')
        context = {
            'authors': authors,
            'publisher_id': 'jdh',
            'journal_code': 'jdh',
            'doi_code': 'jdh',
            'issn': '2747-5271'
        }
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    return render(request, 'jdhseo/dg_template.xml', context, content_type='text/xml')
