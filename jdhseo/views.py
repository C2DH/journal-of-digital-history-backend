import base64
import logging
import requests
import os
import urllib.parse
import marko
import io, zipfile
from urllib.parse import urlparse
from django.http import Http404
from django.shortcuts import render
from jdhapi.models import Article, Issue, Author
from django.conf import settings
from .utils import parseJupyterNotebook, generate_qrcode, merge_authors_affiliations
from .utils import getPlainMetadataFromArticle
from django.http import HttpResponse
from jdhapi.utils.article_xml import ArticleXml, JOURNAL_PUBLISHER_ID, JOURNAL_CODE, DOI_CODE, ISSN
from jdhapi.utils.doi import get_publisher_id, get_doi_url_formatted_jdh
from jdhapi.utils.copyright import CopyrightJDH
from jdhapi.utils.affiliation import get_affiliation_json
from lxml import html
from django.http import FileResponse
from django.template.response import TemplateResponse
from django.http import HttpResponse
from datetime import datetime

logger = logging.getLogger(__name__)


def article_detail(request, pid):
    published_date = ""
    # get ONLY published article matching the pid
    try:
        article = Article.objects.get(
            abstract__pid=pid)
            #status=Article.Status.PUBLISHED)
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
    if 'keywords' in article.data:
        array_keys = "<b>Keywords: </b>" + article.data['keywords'][0].replace(';', ',')
    logger.info(f"keywords {array_keys}")
    # Initialize ArticleXml to get authors and affiliations
    try:
        article_xml = ArticleXml(
            article_authors=article.abstract.authors.all(),
            title=article.data.get('title', [''])[0],
            article_doi=article.doi,
            keywords=article.data.get('keywords', []),
            publication_date=article.publication_date,
            copyright=article.copyright_type,
            issue_pid=article.issue.pid,
            pid=pid
        )
        authors = article_xml.authors
        affiliations = article_xml.affiliations
        merged_authors_affiliations = merge_authors_affiliations(authors, affiliations)
        logger.info(f"merged_authors_affiliations {merged_authors_affiliations}")

    except Http404 as e:
        raise Http404(f"Error initializing ArticleXml: {str(e)}")
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
        'keywords': array_keys,
        'authors': authors,
        'authors_affiliations': merged_authors_affiliations
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
            res = requests.get(remote_url, timeout=10)
            # add NB paragraphs to context
            try:
                notebook_data = res.json()
                context.update({'nb': parseJupyterNotebook(notebook_data, merged_authors_affiliations)})
            except ValueError as e:
                logger.error(f'Error parsing JSON for article pk={article.pk} notebook remote_url={remote_url}')
                logger.exception(e)
                raise Http404(f'Error parsing JSON for article pk={article.pk} notebook remote_url={remote_url}')
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


def issue_detail(request, pid):
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


def issue_xml_dg_view(request, pid):
    context = {
        'journal_publisher_id': JOURNAL_PUBLISHER_ID,
        'journal_code': JOURNAL_CODE,
        'doi_code': DOI_CODE,
        'issn': ISSN,
    }
    return render(request, 'jdhseo/issue_dg.xml', context, content_type='text/xml; charset=utf-8')


def article_xml_dg_view(request, pid):
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
            article_title = html.fromstring(marko.convert(article.data['title'][0])).text_content()
        context = {
            'articleXml': ArticleXml(article.abstract.authors.all(), article_title, article.doi, keywords, article.publication_date, article.copyright_type, article.issue, pid),
            'journal_publisher_id': JOURNAL_PUBLISHER_ID,
            'journal_code': JOURNAL_CODE,
            'doi_code': DOI_CODE,
            'issn': ISSN,
        }
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
        return render(request, 'jdhseo/article_dg.xml', context, content_type='text/xml; charset=utf-8')




def get_article_content_from_url(url, pid):
    response = requests.get(url)
    # Get filename from doi
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    # filename = publisher_id +".open-issue"
    filename = get_publisher_id(article.doi).lower() + ".open-issue"
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext == '.pdf':
        filename = f"/{filename}/{filename}.pdf"
    else:
        filename = f"/{filename}/{filename}.xml"
    return response.content, filename


def get_issue_content_from_url(url, pid):
    """
    Fetches the content of an issue from a given URL and retrieves associated filenames.

    Args:
        url (str): The URL to fetch the issue content from.
        pid (str): The persistent identifier (PID) of the article.

    Returns:
        tuple: A tuple containing the response content, the issue filename, and the issue zip filename.

    Raises:
        Http404: If the article with the given PID does not exist.
    """
    response = requests.get(url)
    # Get filename from doi
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    filename = get_publisher_id(article.doi).lower()
    # convention for the filename_issue: {journal-code}.{issue.publication_date |date:”Y”}.{issue.volume}.issue-{issue.issue}.xml
    issue = article.issue
    publication_year = issue.publication_date.year if issue.publication_date else 'unknown'
    filename_issue = f"/issue-files/{JOURNAL_CODE}.{publication_year}.{issue.volume}.issue-{issue.issue}.xml"
    # {journal_code}_{filename}_oi_YYYY-MM-DD--HH-MM-SS.zip
    timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    filename_zip = f"{JOURNAL_CODE}_{filename}_oi_{timestamp}.zip"
    return response.content, filename_issue, filename_zip


def generate_zip(request, pid):
    logger.info(f"{request.build_absolute_uri()}")
    # The article's package for DG contains : XML and pdf
    # issue xml
    url_issue = f'https://journalofdigitalhistory.org/prerendered/en/issue/dg/{pid}'
    url_xml = f'https://journalofdigitalhistory.org/prerendered/en/article/dg/{pid}'
    url_pdf = f'https://journalofdigitalhistory.org/en/article/{pid}.pdf'
    response_issue, filename_issue, filename_zip = get_issue_content_from_url(url_issue, pid)
    # Create zip
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w')
    for url in [url_xml, url_pdf]:
        response, filename = get_article_content_from_url(url, pid)
        filename = filename.lstrip('/')  # Remove leading slash
        zip_file.writestr(filename, response)
        logger.debug(f"Added {filename} to zip")
    filename_issue = filename_issue.lstrip('/')  # Remove leading slash
    zip_file.writestr(filename_issue, response_issue)
    logger.debug(f"Added {filename_issue} to zip")
    zip_file.close()

    # List all elements in the zip file
    buffer.seek(0)
    with zipfile.ZipFile(buffer, 'r') as z:
        logger.debug("Contents of the zip file:")
        for file_info in z.infolist():
            logger.debug(file_info.filename)

    # Return zip
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={filename_zip}'
    return response

