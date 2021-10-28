import requests
from django.core.management.base import BaseCommand, CommandError
from jdhtasks.tasks import store
from algoliasearch.search_client import SearchClient
from django.conf import settings
from jdhseo.utils import parseJupyterNotebook
from jdhapi.models import Article


class Command(BaseCommand):
    """
    usage:
    ENV=development pipenv run ./manage.py echo
    or if in docker:
    docker exec -it docker_miller_1 \
    python manage.py echo
    """
    def add_arguments(self, parser):
        parser.add_argument('pid', type=str)

    def handle(self, pid, *args, **options):
        self.stdout.write(f'Execute task for pid: {pid}')
        try:
            article = Article.objects.get(
                abstract__pid=pid,
                status=Article.Status.PUBLISHED)
        except Article.DoesNotExist as e:
            raise e
        self.stdout.write(f'loading ipynb: {article.notebook_ipython_url}')
        client = SearchClient.create(
            settings.JDHTASKS_ALGOLIA_APPID,
            settings.JDHTASKS_ALGOLIA_ADMIN_APIKEY)
        index = client.init_index(settings.JDHTASKS_ALGOLIA_INDEX_NAME)

        res = requests.get(article.notebook_ipython_url)
        # add NB paragraphs to context
        ipynb = parseJupyterNotebook(res.json())
        # print(ipynb)
        # save metadata
        item_to_store = {
            'objectID': f'{pid}',
            'title': ipynb['title_plain'],
            'pid': pid,
            'text': ipynb['abstract_plain'],
        }
        index.save_objects([item_to_store])
        # https://www.algolia.com/doc/guides/sending-and-managing-data/prepare-your-data/how-to/indexing-long-documents/
        for i, par in enumerate(ipynb['paragraphs']):
            item_to_store = {
                'objectID': f'{pid}-c{i}',
                'title': ipynb['title_plain'],
                'pid': pid,
                'text': par
            }
            index.save_objects([item_to_store])
        # test
        # objects = index.search('Fo')
        # print(objects)
        # try:
        #     store.delay(pid=pid)
        # except Exception as e:
        #     raise CommandError(e)
        # else:
        #     self.stdout.write('Execute task done.')
