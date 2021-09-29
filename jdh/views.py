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


logger = logging.getLogger(__name__)


class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        template = get_template('abstract.html')
        context = {
                "invoice_id": 123,
                "customer_name": "John Cooper",
                "amount": 1399.99,
                "today": "Today",
        }
        html = template.render(context)
        pdf = render_to_pdf('abstract.html', context)
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


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        sUrl = settings.STATIC_URL        # Typically /static/
        sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL         # Typically /media/
        mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception('media URI must start with %s or %s' % (sUrl, mUrl))
        return path


""" def get(self, request, *args, **kwargs):
    template_path = 'test-image.html'
    context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response """