from django.http import HttpResponse
from django.views.generic import View
from .utils import render_to_pdf
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
import logging
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from jdhapi.models import Abstract, Article
from django.shortcuts import render, get_object_or_404

logger = logging.getLogger(__name__)


class GeneratePDF(View):
    def get(self, request, pid, *args, **kwargs):
        abstract = get_object_or_404(Abstract, pid=pid)
        article = get_object_or_404(Article, abstract=abstract)
        template_file = 'abstract.html'
        template = get_template(template_file)
        abstract_text = article.data['abstract'][0]
        first_caracter = abstract_text[0:1]
        context = {
            "article_title": abstract.title,
            "article_authors": abstract.contact_firstname + " " + abstract.contact_lastname,
            "article_authors_affiliation": abstract.contact_affiliation,
            "article_keywords": article.data['keywords'][0],
            "article_abstract_first_letter": first_caracter,
            "article_abstract": abstract_text[1:],
        }
        html = template.render(context)
        pdf = render_to_pdf(template_file, context)
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




