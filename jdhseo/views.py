import base64
import logging
import requests
import urllib.parse
from django.http import Http404
from django.shortcuts import render
from jdhapi.models import Article
from django.conf import settings
from .utils import parseJupyterNotebook

logger = logging.getLogger(__name__)


def ArticleDetail(request, pid):
    # get ONLY published article matching the pid
    try:
        article = Article.objects.get(
            abstract__pid=pid,
            status=Article.Status.PUBLISHED)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    # decode notebook url
    notebook_url = urllib.parse.unquote(
        base64.b64decode(article.notebook_url).decode('utf-8'))
    # fill the context for the template file.
    context = {'article': article}
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
            context.update({'nb': parseJupyterNotebook(res.json())})
        except Exception as e:
            logger.error(f'Error occurred on article pk={article.pk} notebook')
            logger.exception(e)
            raise Http404("Article Notebook file not found (or not valid)")
    else:
        logger.error(
            f'Article(pid={pid}).notebook_url is BAD:"{notebook_url}"')
        raise Http404("Article does not exist")
    # get content from notebook_url using our proxy
    # r = requests.get('https://api.github.com/user')
    return render(request, 'jdhseo/article_detail.html', context)