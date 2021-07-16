from django.core.management.base import BaseCommand, CommandError
from jdhtasks.tasks import echo


class Command(BaseCommand):
    """
    usage:
    ENV=development pipenv run ./manage.py echo
    or if in docker:
    docker exec -it docker_miller_1 \
    python manage.py echo
    """
    def add_arguments(self, parser):
        parser.add_argument('message', type=str)

    def handle(self, message, *args, **options):
        self.stdout.write(f'Echo execute task "echo" for message: {message}')
        try:
            echo.delay(message=message)
        except Exception as e:
            raise CommandError(e)
        else:
            self.stdout.write('Echo execute task "echo" success.')
