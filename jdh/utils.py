import os
import logging
import base64
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import get_template
from django.conf import settings
from django.contrib.staticfiles import finders


logger = logging.getLogger(__name__)

""" def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None """


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
            logger.info(f'uri: {uri}')
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
            logger.info(f'path: {path}')
        else:
            return uri

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception('media URI must start with %s or %s' % (sUrl, mUrl))
        return path


def render_to_pdf(template_src, context_dict):

    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result,
                            encoding='UTF-8', link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def generate_qrcode(pid):
    buffer = BytesIO()
    input_data = "https://journalofdigitalhistory.org/en/article/"
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5)

    qr.add_data(input_data)
    qr.make(fit=True)
    # code hex 00F5D4
    img = qr.make_image(back_color=(255, 255, 255), fill_color=(0, 245, 212))
    img.save(buffer, format="PNG")
    typeEncode = "data:image/png;base64,"
    # base64Encode = "iVBORw0KGgoAAAANSUhEUgAAAZoAAAGaAQAAAAAefbjOAAAC3UlEQVR4nO2cQYrjMBBFX40NvVSgD9BHsa82R+ob2EfpAwzIy4BMzUIlRUkPDA09SUYuL4wT+xEZf0r1S+WI8uVt/fF1BhxyyCGHHHLIoT4hsW0ENhHYRmRmF5nZBbZywfyQ4Tl0RwhVVWVSVdU4qKommDQBDJp3Uz5Rrlue/J4c+g5oswAg8/aiumwvyqQJXcJZdAEsgjxoeA7dDRo/f7WLEhIK+8j0MSLT+6OG59ATQCEh8yYi8zaiP98SuvybX3LoGaESI4ICG7Ceosr6pgCKEIZcw2orWU9+Tw59A7SKiMgJmD7GvJN5q0fs2Wo8angO3TtGtAEgnEUh2af1hFgEecTwHLo7VNxnBGAwC7owqC4hoRqHq7PuPnuHsIccEkyqCkGzIkwHWRZYeun1iO4hU4RGq0ZlbQDoEtQqVBSBeIzoH2pmjSKGoYaMVK8yw+Exon/IFAFgxeoIRSAWPyAk8s4V0T3UzBoWI8quLGSUPCJLxRXRO9TECHvwda6YLq4DMG24InqHykOm5BGt00y36aUron+ozBqaclCwdCFCazyrN/VZo3uozSNqFpkjwxShySNyjcIV0TtUZw2zGY0YyEe1iyZ6PeIIUMksg00Jtos1Z2iqVh4jjgA1VWxrgwjamAtyUun1iONAV+7zEi3ipUiZKBbUY8QRIOuYmRaQ6f2U18V1fTuLAgjbq8oUX4HwS/Tew3Po7tBVaTLPH/bRStl1hdxrlseAGkVAYzgSOaPQ2C5yuSL6h2qFyrYrw4Gll9V/uCL6h3IeURooh6RrPt5HYChLHNtrPvI8on/o9p2usr51sR61uQqvUB0J2upLneEs2YLaiRdlFcnf2SX/yT059D1QfQlYTrvk1mxbAN29O/8AUNuLXdc+SyNVsR51wcNnjf6hP7wbriWPiOZDS1nT+yOOALV9lvWfASy9bKKFNVe5IvqHRP9+ze3m/0zmkEMOOeSQQw4B/AbOLPLhVmPyigAAAABJRU5ErkJggg=="
    base64Encode = base64.b64encode(buffer.getvalue()).decode("utf-8")
    srcImage = typeEncode + base64Encode
    return srcImage
