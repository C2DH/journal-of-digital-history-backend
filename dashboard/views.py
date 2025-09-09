import logging
import re
import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from jdhapi.models import Abstract


logger = logging.getLogger(__name__)


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
