from django.core.management.base import BaseCommand, CommandError
from jdhapi.tasks import send_confirmation


class Command(BaseCommand):
    """
    usage:
    ENV=development pipenv run ./manage.py celery_test
    or if in docker:
    docker exec -it docker_miller_1 \
    python manage.py celery_test
    """
    def handle(self, *args, **options):
        self.stdout.write('celery_test execute task "add"...')
        try:
            send_confirmation.delay()
        except Exception as e:
            raise CommandError(e)
