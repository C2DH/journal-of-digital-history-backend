from django.shortcuts import render
from django.views.generic import CreateView
from django.http import HttpResponse
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from jdhapi.models import Abstract
from dashboard.forms import EmailConfigurationForm
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import CreateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
import imaplib
import time


def getDefaultSubject(abstractsubmission):
    defaultSubject = abstractsubmission.title
    return defaultSubject


def getDefaultBody(abstractsubmission):
    defaultBody = "Dear " + abstractsubmission.contact_firstname + " " + abstractsubmission.contact_lastname + "\n\n" + "We're sorry, we were unable to proceed with your article submission as it is. \nWe encouage you to review the methodology point. \nBest regards, \n\nFrédéric Clavert"
    return defaultBody


def sendmail(subject, body, sent_to):
    try:
        send_mail(
            subject,
            body,
            'jdh.admin@uni.lu',
            [sent_to, 'jdh.admin@uni.lu'],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@staff_member_required
def home(request):
    return render(request, 'dashboard/home.html')


@staff_member_required
def abstractSubmissions(request):
    abstractsubmissions = Abstract.objects.all()
    return render(request, 'dashboard/abstract_submissions.html', {'abstractsubmissions': abstractsubmissions})


@staff_member_required
def abstract(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    return render(request, 'dashboard/abstract_detail.html', {'abstractsubmission': abstractsubmission})


def validated(request, pk, STATUS):
    defaultSubject = ""
    defaultBody = ""
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    sent_to = abstractsubmission.contact_email
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = EmailConfigurationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            cd = form.cleaned_data
            subject = cd.get('subject')
            body = cd.get('body')
            # not resubmit mail in case of refresh
            if (abstractsubmission.status == Abstract.Status.SUBMITTED):
                # send email
                sendmail(subject, body, sent_to)
                # set the status
                if STATUS == Abstract.Status.DECLINED:
                    abstractsubmission.declined()
                if STATUS == Abstract.Status.ACCEPTED:
                    abstractsubmission.accepted()
            # redirect to a new URL:
            abstractsubmissions = Abstract.objects.all()
            return render(request, 'dashboard/abstract_submissions.html', {'abstractsubmissions': abstractsubmissions})
            # return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        # Initialize some value
        if STATUS == Abstract.Status.DECLINED:
            defaultSubject = getDefaultSubject(abstractsubmission)
            defaultBody = getDefaultBody(abstractsubmission)
        if STATUS == Abstract.Status.ACCEPTED:
            defaultSubject = getDefaultSubject(abstractsubmission)
            defaultBody = "ACCEPTED"
        form = EmailConfigurationForm(initial={'subject': defaultSubject, 'body': defaultBody})
    return render(request, 'dashboard/email_configuration.html', {'form': form, 'abstractsubmission': abstractsubmission})


@staff_member_required
def declined(request, pk):
    return validated(request, pk, Abstract.Status.DECLINED)


@staff_member_required
def accepted(request, pk):
    return validated(request, pk, Abstract.Status.ACCEPTED)


@staff_member_required
def abandoned(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    abstractsubmission.abandoned()
    # redirect to a new URL:
    abstractsubmissions = Abstract.objects.all()
    return render(request, 'dashboard/abstract_submissions.html', {'abstractsubmissions': abstractsubmissions})
