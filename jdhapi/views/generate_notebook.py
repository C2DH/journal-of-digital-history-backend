from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from jdhapi.models import Abstract
from rest_framework.response import Response

@api_view(['GET'])
def GenerateNotebook(request, pid):
    abstractsubmission = get_object_or_404(Abstract, pid=pid)
    return Response({
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {
            "jdh": {
                "pid": abstractsubmission.pid
            }
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "jdh": {
                        "section": "title"
                    }
                },
                "source": abstractsubmission.title.split('\n')
            }
        ]
    })