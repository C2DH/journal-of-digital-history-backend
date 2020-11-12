from django.shortcuts import render
from django.views.generic import CreateView
from django.http import HttpResponse
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from . models import AbstractSubmission, Status
from dashboard.forms import  EmailConfigurationForm
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import CreateView
import imaplib, time


def home(request):
    abstractsubmissions = AbstractSubmission.objects.all()
    return render(request,'dashboard/home.html',{'abstractsubmissions': abstractsubmissions})


def abstract(request, pk):
    abstractsubmission = get_object_or_404(AbstractSubmission, pk=pk)
    return render(request, 'dashboard/abstract_detail.html', {'abstractsubmission': abstractsubmission})


def getDefaultSubject(abstractsubmission):
    defaultSubject = abstractsubmission.title
    return defaultSubject 

def getDefaultBody(abstractsubmission):
    defaultBody = "Dear " + abstractsubmission.submitter_firstname + " " + abstractsubmission.submitter_lastname + "\n" + "We're sorry, we were unable to proceed with your article submission as it is. \nWe encouage you to review the methodology point. \nBest regards, \nFrédéric Clavert"
    return defaultBody 

def validated(request, pk, STATUS):
    abstractsubmission = get_object_or_404(AbstractSubmission, pk=pk) 
    sent_to = abstractsubmission.submitter_email
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
            # send email          
            sendmail(subject, body,sent_to)
            # set the status
            if STATUS == Status.DECLINED:
                abstractsubmission.declined()
            if STATUS == Status.ACCEPTED:
                abstractsubmission.accepted()
            # redirect to a new URL:
            abstractsubmissions = AbstractSubmission.objects.all()
            return render(request,'dashboard/home.html',{'abstractsubmissions': abstractsubmissions})
            #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        # Initialize some value
        if STATUS == Status.DECLINED:
            defaultSubject = getDefaultSubject(abstractsubmission)
            defaultBody = getDefaultBody(abstractsubmission)  
        if STATUS == Status.ACCEPTED:
            defaultSubject = getDefaultSubject(abstractsubmission)
            defaultBody = "ACCEPTED"
        form = EmailConfigurationForm(initial={'subject': defaultSubject, 'body': defaultBody})
    return render(request, 'dashboard/email_configuration.html', {'form': form, 'abstractsubmission' : abstractsubmission})

def declined(request, pk):
    return validated(request, pk, Status.DECLINED)


def accepted(request, pk):
    return validated(request, pk, Status.ACCEPTED)

def sendmail(subject, body, sent_to):
    try:
        send_mail(
            subject,
            body,
            'jdh.admin@uni.lu',
            [sent_to,'jdh.admin@uni.lu'],
            fail_silently=False,
        )
    except Exception as e:
        print(e)

