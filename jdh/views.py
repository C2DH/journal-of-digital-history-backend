from django.http import HttpResponse
from django.views.generic import View
from .utils import render_to_pdf, generate_qrcode
from django.template.loader import get_template
from xhtml2pdf import pisa
import base64
import os
import logging
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from jdhapi.models import Abstract, Article
from django.shortcuts import render, get_object_or_404
import urllib.parse
from jdhseo.utils import parseJupyterNotebook
import requests

logger = logging.getLogger(__name__)


class GeneratePDF(View):
    def get(self, request, pid, *args, **kwargs):
        abstract = get_object_or_404(Abstract, pid=pid)
        article = get_object_or_404(Article, abstract=abstract)
        template_file = 'article_detail.html'
        template = get_template(template_file)
        abstract_text = article.data['abstract'][0]
        first_caracter = abstract_text[0:1]
        qrCodebase64 = generate_qrcode(pid)
        context = {
            'article': article,
            'qr_code': qrCodebase64
        }
        # decode notebook url
        notebook_url = urllib.parse.unquote(
            base64.b64decode(article.notebook_url).decode('utf-8'))
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
        html = template.render(context)
        pdf = render_to_pdf(template_file, context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "abstract_%s.pdf" % (pid)
            content = "inline;filename=%s" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename=%s" % (filename)
                response['Content-Disposition'] = content
            return response
            # return HttpResponse(pdf, content_type='application/pdf')
        return HttpResponse("Not found")



"""def get(self, request, *args, **kwargs):
    #template = get_template('test-image.html')
     context = {
                "invoice_id": 123,
                "customer_name": "John Cooper",
                "amount": 1399.99,
                "today": "Today",
    }
    html = template.render(context)

    template_path = 'test-image.html'
    context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    #pdf = render_to_pdf('test-image.html', context)
    pdf = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "abstract_%s.pdf" % ("12345")
        content = "inline;filename=%s" % (filename)
        download = request.GET.get("download")
        if download:
            content = "attachment; filename=%s" % (filename)
            response['Content-Disposition'] = content
        return response
        # return HttpResponse(pdf, content_type='application/pdf')
    return HttpResponse("Not found") """




