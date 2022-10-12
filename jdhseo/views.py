import base64
import logging
import requests
import urllib.parse
from django.http import Http404
from django.shortcuts import render
from jdhapi.models import Article, Issue, Author
from django.conf import settings
from .utils import parseJupyterNotebook, generate_qrcode
from .utils import getPlainMetadataFromArticle
from django.http import HttpResponse
from jdhapi.utils.article_xml import ArticleXml
from jdhapi.utils.doi import get_publisher_id, get_doi_url_formatted_jdh
from jdhapi.utils.copyright import CopyrightJDH
from jdhapi.utils.affiliation import get_affiliation_json
import marko
from lxml import html
from django.http import FileResponse
from django.template.response import TemplateResponse
import io, zipfile
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
    doi_url = get_doi_url_formatted_jdh(article.doi)
    # Publish online
    if (article.publication_date):
        published_date = article.publication_date.date()
    # decode notebook url
    notebook_url = urllib.parse.unquote(
        base64.b64decode(article.notebook_url).decode('utf-8'))
    # contact_orcid
    ORCID_URL = "https://orcid.org/"
    contact_orcid = article.abstract.contact_orcid.partition(ORCID_URL)[2]
    if 'keywords' in article.data:
        array_keys = "<b>Keywords: </b>" + article.data['keywords'][0].replace(';', ',')
    logger.info(f"keywords {array_keys}")
    # fill the context for the template file.
    context = {
        'article': article,
        'article_absolute_url':
            f"https://journalofdigitalhistory.org/en/article/"
            f"{article.abstract.pid}",
        'qr_code': qrCodebase64,
        'media_url': settings.MEDIA_URL,
        'doi_url': doi_url,
        'published_date': published_date,
        'keywords': array_keys
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
        logger.debug(f'Belongs to issue {article.issue}')
        keywords = []
        if 'keywords' in article.data:
            array_keys = article.data['keywords'][0].replace(';', ',').split(',')
            for item in array_keys:
                keyword = {
                    "keyword": item,
                }
                keywords.append(keyword)
        if 'title' in article.data:
            articleTitle = html.fromstring(marko.convert(article.data['title'][0])).text_content()
        context = {
            'articleXml': ArticleXml(article.abstract.authors.all(), articleTitle, article.doi, keywords, article.publication_date, article.copyright_type, article.issue, pid),
            'journal_publisher_id': 'jdh',
            'journal_code': 'jdh',
            'doi_code': 'jdh',
            'issn': '2747-5271',
        }
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    # response = render(request, 'jdhseo/dg_template.xml', context, content_type='application/xml')
    # response['Content-Disposition'] = 'attachment; filename="test.xml"'
    # return response
    return render(request, 'jdhseo/dg_template.xml', context, content_type='text/xml; charset=utf-8')


def Generate_zip(request, pid):
    # The article's package for DG contains : XML and pdf
    # pdf
    url_pdf = 'https://journalofdigitalhistory.org/en/article/' + pid + '.pdf'
    response_pdf = requests.get(url_pdf)
    # XML
    url_XML = 'https://journalofdigitalhistory.org/prerendered/en/article/dg/' + pid
    response_xml = requests.get(url_XML)
    # Get filename from doi
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    filename = get_publisher_id(article.doi).lower()
    filename_pdf = filename + ".pdf"
    filename_xml = filename + ".xml"
    filename_zip = filename + ".zip"
    # filename = os.path.split(url)[1]
    # Create zip
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w')
    zip_file.writestr(filename_pdf, response_pdf.content)
    zip_file.writestr(filename_xml, response_xml.content)
    zip_file.close()
    # Return zip
    response = HttpResponse(buffer.getvalue())
    response['Content-Type'] = 'application/x-zip-compressed'
    response['Content-Disposition'] = f'attachment; filename={filename_zip}'
    return response


