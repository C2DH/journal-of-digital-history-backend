import json
from django.core.management.base import BaseCommand, CommandError
from jdhapi.models import Article
from jdhapi.utils.articleUtils import get_notebook_stats


class Command(BaseCommand):
    """
    usage:
    pipenv run ./manage.py fingerprint <article_id>
    or if in our docker:
    docker exec -it journal-digital-history-docker-stack_backend_1 \
    python manage.py fingerprint <article_id>
    """

    help = 'Retrieve the JDH fingerprint for the given Article instance'

    def add_arguments(self, parser):
        parser.add_argument('article_ids', nargs='+', type=int)

    def handle(self, article_ids, *args, **options):
        self.stdout.write(
            f'Start "fingerprint" command for article_ids {article_ids}...')
        for article_id in article_ids:
            try:
                article = Article.objects.get(pk=article_id)
            except Article.DoesNotExist:
                raise CommandError(f'Article "{article_id}" does not exist')
            self.stdout.write(
                f'loading fingerprint for article Article "{article.pk}", '
                f'pid: {article.abstract.pid}...')
            self.stdout.write(
                f'repository_url: {article.repository_url}...')
        result = get_notebook_stats(repository_url=article.repository_url)
        self.stdout.write(f'result:{json.dumps(result, indent=2)}')
        # try:
        #     send_confirmation.delay()
        # except Exception as e:
        #     raise CommandError(e)
