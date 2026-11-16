# jdhbackend

backend for our Journal of Digital History

## development (with pipenv)

First of all, make sure that pipenvlock and requirements.txt are synced, then
start the JDH django apps using make.

```
pipenv install -r requirements.txt

make run-dev
```

` pipenv install -r requirements.txt` will update the pipfile according to the `requirements.txt` file.

### SEO configuration in development

THe django app `jdhseo` needs a JDHSEO_PROXY_HOST env variable in the full form
**without the trailing slash** like `https://local-proxy-domain-name`.
Plain `http` protocol can also be used.
The domain name provided should correctly handle the `/proxy-githubusercontent`
path.
By default this value is set to `https://journalofdigitalhistory.org`

### Celery tasks in development

The django app `jdhtasks` is a separate app that should contain all celery tasks.
However, as we use `autodiscover_tasks`, tasks can be added in each app.
As Celery runs together with redis, you have to provide a redis-server somehow.
I suggest to start fresh and use docker:

```
docker run --name jdh-redis -p 6379:6379 -d redis:alpine
```

Then run

```
REDIS_HOST=localhost REDIS_PORT=6379 \
pipenv run celery -A jdhtasks worker -l info
```

to start the celery worker using `pipenv` and your current `.env` file.

To test that everything works fine run in another terminal:

```
REDIS_HOST=localhost REDIS_PORT=6379 \
pipenv run ./manage.py echo "It was a bright cold day in July ..."
```

(source file for this command is at `jdhtasks/management/commands/echo.py`)

### Running tests

Be sure to have your environment activate (if not, do `source .venv/bin/activate`) and then to run ALL the tests :

`python3 manage.py test`

or with Pip:

`pipenv run ./manage.py test`

If you want to run a specific test file (eg. `test_check_github_id`) :

`python3 manage.py test tests.jdhapi.views.test_check_github_id`

with Pip :

`pipenv run ./manage.py test tests.jdhapi.views.test_check_github_id`

### To generate requirements.txt from the pipfile

`pipenv requirements --dev --exclude-markers > requirements.txt`

### Actions tracking : History tables

Two models for our database are concerned by the history tracking : **Abstract** and **Article**. For tracking every actions, we use a Django library named [django-simple-history](https://github.com/django-commons/django-simple-history). The implementation is made through this code line in both models :

```python
history = HistoricalRecords()
```

Then the records are presented in each corresponding serializer with `def get_status_log(self,obj)` method with for each status change : **the date**, **the user** who made the change, **the status** selected for the change.

```python
    {
        "date": string
        "user": string
        "status": string
    }
```

For populating the database, on the first sight, with no previous history, you can use :

`uv run python manage.py populate_history --auto`

For removing old history, for instance all the entries which are older than 30 days, you can do :

`uv run python manage.py clean_old_history --days 30 --auto`
