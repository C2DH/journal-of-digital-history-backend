from django.core.mail import send_mail
from jdhapi.models import Abstract, Article

from jdhapi.forms import EmailConfigurationForm
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
import logging
import requests
import re


logger = logging.getLogger(__name__)


def getDefaultSubject(abstractsubmission):
    defaultSubject = abstractsubmission.title
    return defaultSubject


def getDefaultBody(abstractsubmission):
    defaultBody = (
        "Dear "
        + abstractsubmission.contact_firstname
        + " "
        + abstractsubmission.contact_lastname
        + "\n\n"
        + "We're sorry, we were unable to proceed with your article submission"
        + "as it is. \nWe encouage you to review the methodology point."
        + "\nBest regards, \n\nFrédéric Clavert"
    )
    return defaultBody


def sendmail(subject, body, sent_to):
    try:
        send_mail(
            subject,
            body,
            "jdh.admin@uni.lu",
            [sent_to, "jdh.admin@uni.lu"],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@staff_member_required
def home(request):
    return render(request, "dashboard/home.html")


def validAbstracts():
    abstractsubmissions = []
    # Exclude if ABANDONNED- if DECLINED
    abstracts = (
        Abstract.objects.exclude(status=Abstract.Status.ABANDONED)
        .exclude(status=Abstract.Status.DECLINED)
        .exclude(status=Abstract.Status.SUSPENDED)
    )
    for abstract in abstracts:
        article = Article.objects.filter(
            abstract__pid=abstract.pid, status=Article.Status.PUBLISHED
        ).first()
        if not article:
            # abstract without article created
            abstractsubmissions.append(abstract)
    return abstractsubmissions


@staff_member_required
def abstractSubmissions(request):
    abstractsubmissions = validAbstracts()
    return render(
        request,
        "dashboard/abstract_submissions.html",
        {"abstractsubmissions": abstractsubmissions},
    )


@staff_member_required
def abstract(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    return render(
        request,
        "dashboard/abstract_detail.html",
        {"abstractsubmission": abstractsubmission},
    )


def validated(request, pk, STATUS):
    defaultSubject = ""
    defaultBody = ""
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    sent_to = abstractsubmission.contact_email
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = EmailConfigurationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            cd = form.cleaned_data
            subject = cd.get("subject")
            body = cd.get("body")
            # not resubmit mail in case of refresh
            if abstractsubmission.status == Abstract.Status.SUBMITTED:
                # send email
                sendmail(subject, body, sent_to)
                # set the status
                if STATUS == Abstract.Status.DECLINED:
                    abstractsubmission.declined()
                if STATUS == Abstract.Status.ACCEPTED:
                    abstractsubmission.accepted()
            # redirect to a new URL:
            abstractsubmissions = Abstract.objects.all()
            return render(
                request,
                "dashboard/abstract_submissions.html",
                {"abstractsubmissions": abstractsubmissions},
            )
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
        form = EmailConfigurationForm(
            initial={"subject": defaultSubject, "body": defaultBody}
        )
    return render(
        request,
        "dashboard/email_configuration.html",
        {"form": form, "abstractsubmission": abstractsubmission},
    )


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
    abstractsubmissions = validAbstracts()
    return render(
        request,
        "dashboard/abstract_submissions.html",
        {"abstractsubmissions": abstractsubmissions},
    )


@staff_member_required
def suspended(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    abstractsubmission.suspended()
    # redirect to a new URL:
    abstractsubmissions = validAbstracts()
    return render(
        request,
        "dashboard/abstract_submissions.html",
        {"abstractsubmissions": abstractsubmissions},
    )


@staff_member_required
def fingerprint(request, pk):
    abstractsubmission = get_object_or_404(Abstract, pk=pk)
    article = abstractsubmission.article
    # url of type
    RAW_GIT = "https://raw.githubusercontent.com"
    GIT_USER = "jdh-observer"
    gitRepo = article.issue.pid + "-" + article.abstract.pid
    notebookPath = article.notebook_path
    rawUrl = RAW_GIT + "/" + GIT_USER + "/" + gitRepo + "/main/" + notebookPath
    try:
        generateStat(article, rawUrl)(article, rawUrl)
    except Exception as e:
        print(rawUrl)
        print(e)
    # redirect to a new URL:
    return render(
        request,
        "dashboard/abstract_detail.html",
        {"abstractsubmission": abstractsubmission, "article": article},
    )


def generateStat(article, rawUrl):
    r = requests.get(rawUrl)
    notebook = r.json()
    # use the cached response
    cells = notebook.get("cells")
    # output
    cells_stats = []
    for cell in cells:
        c = {"type": cell["cell_type"]}
        # just skip if it's empty
        source = cell.get("source", [])
        if not source:
            continue
            # check cell metadata
        tags = cell.get("metadata").get("tags", [])
        if "hidden" in tags:
            continue
        c["countLines"] = len(source)
        c["countChars"] = len("".join(source))
        c["tags"] = tags
        # c['source'] = cell.get('source')
        c["isMetadata"] = any(
            tag in ["title", "abstract", "contributor", "disclaimer"] for tag in tags
        )
        c["isHermeneutic"] = any(
            tag in ["hermeneutics", "hermeneutics-step"] for tag in tags
        )
        c["isFigure"] = any(tag.startswith("figure-") for tag in tags)
        c["isFullWidth"] = any(tag == "full-width" for tag in tags)
        c["isHeading"] = (
            cell["cell_type"] == "markdown"
            and re.match(r"\s*#+\s", "".join(cell.get("source"))) is not None
        )
        cells_stats.append(c)
    general_stats = {
        "countLines": sum([c["countLines"] for c in cells_stats]),
        "countChars": sum([c["countChars"] for c in cells_stats]),
        "countContributors": sum(
            ["contributor" in c["tags"] for c in cells_stats],
        ),
        "countHeadings": sum([c["isHeading"] for c in cells_stats]),
        "countHermeneuticCells": sum(
            [c["isHermeneutic"] for c in cells_stats],
        ),
        "countHermeneuticOnlyCells": sum(
            ["hermeneutics" in c["tags"] for c in cells_stats]
        ),
        "countCodeCells": sum([c["type"] == "code" for c in cells_stats]),
        "countCells": len(cells_stats),
        "extentChars": [
            min([c["countChars"] for c in cells_stats]),
            max([c["countChars"] for c in cells_stats]),
        ],
        "extentLines": [
            min([c["countLines"] for c in cells_stats]),
            max([c["countLines"] for c in cells_stats]),
        ],
    }
    article.data = {"stats": general_stats, "cells": cells_stats}
    article.save()
