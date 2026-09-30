"""
Anonymize personal and editorial content data in the database.

Replaces PII on Author records (name, email, orcid, affiliation, social ids,
city, country) and content/PII on Abstract records (title, abstract,
primary contact name/email/affiliation) with deterministic fake data.

Usage:
    uv run manage.py anonymize_db --yes            # actually anonymise
    uv run manage.py anonymize_db --dry-run.       # preview

Safety:
    - Refuses to run unless --yes is passed or the user confirms interactively.
    - Refuses to run when DEBUG is False, unless --force is also passed,
      to avoid accidentally anonymizing a production database.
"""

import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from jdhapi.models import Abstract, Article, Author, Dataset

FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Jamie",
    "Avery",
    "Quinn",
    "Rowan",
    "Skyler",
    "Reese",
    "Emerson",
    "Dakota",
    "Hayden",
    "Finley",
    "Sasha",
    "Charlie",
    "Elliot",
    "Robin",
    "Julie",
    "Carole",
    "Virginie",
    "Sarah",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]

AFFILIATIONS = [
    "University of Example",
    "Institute of Digital Studies",
    "National Research Center",
    "Example State University",
    "Center for Historical Research",
    "Polytechnic of Somewhere",
    "Academy of Applied Sciences",
]

CITIES = [
    "Springfield",
    "Riverside",
    "Fairview",
    "Greenville",
    "Salem",
    "Georgetown",
    "Clinton",
    "Madison",
    "Franklin",
    "Arlington",
]

COUNTRY_CODES = ["US", "GB", "FR", "DE", "LU", "BE", "NL", "IT", "ES", "CA"]

LOREM_WORDS = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "in",
    "reprehenderit",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "dolore",
    "eu",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
]

DATASET_URLS = [
    "http://github.com/octopus/my-dataset",
    "http://github.com/researcher-name/history-dataset",
    "http://data.com/digital-dataset",
]


def _lorem_sentence(rng, min_words=6, max_words=14):
    n = rng.randint(min_words, max_words)
    words = rng.choices(LOREM_WORDS, k=n)
    sentence = " ".join(words)
    return sentence[0].upper() + sentence[1:] + "."


def _lorem_paragraph(rng, sentences=6):
    return " ".join(_lorem_sentence(rng) for _ in range(sentences))


class Command(BaseCommand):
    help = "Anonymize author names/primary_contact and abstract title/abstract/contact fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Do not prompt for interactive confirmation.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running even when DEBUG is False.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print how many rows would be affected, change nothing.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Seed for the random generator, for reproducible output.",
        )

    def handle(self, *args, **options):
        author_count = Author.objects.count()
        abstract_count = Abstract.objects.count()
        article_count = Article.objects.count()
        dataset_count = Dataset.objects.count()

        if options["dry_run"]:
            self.stdout.write(
                f"Dry run: would anonymize {author_count} authors and "
                f"{abstract_count} abstracts. No changes made."
            )
            return

        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG is False. Refusing to anonymize what looks like a "
                "production database. Pass --force to override."
            )

        if not options["yes"]:
            answer = input(
                f"This will irreversibly overwrite {author_count} authors, {dataset_count} datasets"
                f", {article_count} articles and {abstract_count} abstracts with fake data. Type 'yes' to continue: "
            )
            if answer.strip().lower() != "yes":
                self.stdout.write("Aborted.")
                return

        rng = random.Random(options["seed"])

        with transaction.atomic():
            self._anonymize_authors(rng)
            self._anonymize_abstracts(rng)
            self._anonymize_articles(rng)
            self._anonymize_datasets(rng)

        self.stdout.write(
            self.style.SUCCESS(
                f"Anonymized {author_count} authors, {abstract_count} abstracts, {article_count} articles"
                f" and {dataset_count} datasets."
            )
        )

    def _anonymize_authors(self, rng):
        authors = list(Author.objects.all())
        for author in authors:
            firstname = rng.choice(FIRST_NAMES)
            lastname = rng.choice(LAST_NAMES)
            author.firstname = firstname
            author.lastname = lastname
            author.email = f"author{author.id}@example.com"
            author.orcid = (
                f"0000-0000-{author.id % 10000:04d}-{rng.randint(0, 9999):04d}"
            )
            author.affiliation = rng.choice(AFFILIATIONS)
            author.github_id = f"user{author.id}"
            author.bluesky_id = f"user{author.id}.bsky.social"
            author.facebook_id = f"user{author.id}"
            author.linkedin_id = f"user{author.id}"
            author.city = rng.choice(CITIES)
            author.country = rng.choice(COUNTRY_CODES)

        Author.objects.bulk_update(
            authors,
            [
                "firstname",
                "lastname",
                "email",
                "orcid",
                "affiliation",
                "github_id",
                "bluesky_id",
                "facebook_id",
                "linkedin_id",
                "city",
                "country",
            ],
            batch_size=500,
        )

    def _anonymize_abstracts(self, rng):
        abstracts = list(Abstract.objects.all())
        for abstract in abstracts:
            firstname = rng.choice(FIRST_NAMES)
            lastname = rng.choice(LAST_NAMES)
            abstract.title = _lorem_sentence(rng, min_words=4, max_words=10).rstrip(".")
            abstract.abstract = _lorem_paragraph(rng)
            abstract.contact_firstname = firstname
            abstract.contact_lastname = lastname
            abstract.contact_email = f"contact{abstract.id}@example.com"
            abstract.contact_affiliation = rng.choice(AFFILIATIONS)

        Abstract.objects.bulk_update(
            abstracts,
            [
                "title",
                "abstract",
                "contact_firstname",
                "contact_lastname",
                "contact_email",
                "contact_affiliation",
            ],
            batch_size=500,
        )

    def _anonymize_articles(self, rng):
        articles = list(Article.objects.all())
        for article in articles:
            if article.data:
                data = {
                    "title": [article.abstract.title],
                    "abstract": [article.abstract.abstract],
                }
                article.data = data

        Article.objects.bulk_update(articles, ["data"], batch_size=200)

    def _anonymize_datasets(self, rng):
        datasets = list(Dataset.objects.all())
        for dataset in datasets:
            dataset.url = rng.choice(DATASET_URLS)
            dataset.description = _lorem_sentence(
                rng, min_words=4, max_words=10
            ).rstrip(".")

        Dataset.objects.bulk_update(datasets, ["url", "description"], batch_size=200)
