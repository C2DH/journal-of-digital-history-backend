# Create your tasks here

from celery import shared_task
from jdhapi.models import Abstract
from django.core.mail import send_mail


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def count_abstracts():
    return Abstract.objects.count()


@shared_task
def send_confirmation():
    send_mail(
            "test subject",
            "test body",
            'jdh.admin@uni.lu',
            ['elisabeth.guerard@uni.lu'],
            fail_silently=False,
        )
