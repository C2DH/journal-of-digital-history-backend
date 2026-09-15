---
name: python-testing
description: "Guide for writing Django/unittest tests in this repository. Use when asked to create or update a test, write a unit test for a function/task/view, or implement tests described in a GitHub issue."
---

# Python Testing (Django / unittest)

## When to Use

- Asked to write a test for a function, Celery task, admin customization, view, or serializer.
- Asked to implement tests described in a GitHub issue.
- Asked to fix a failing/flaky test after a code change.

## Conventions in this repository

- **Test runner**: Django's `TestCase` (built on `unittest`), run via:

  ```
  python3 manage.py test
  ```

  or a single file/class:

  ```
  python3 manage.py test tests.jdhapi.test_tasks
  ```

- **File location mirrors source layout** under `tests/`, not next to the source file:
  - `jdhapi/tasks.py` → `tests/jdhapi/test_tasks.py`
  - `jdhapi/utils/ojs.py` → `tests/jdhapi/utils/test_ojs_utils.py`
  - `jdhapi/admin.py` → `tests/jdhapi/test_admin.py`
    Match this pattern for any new test file (module path under `tests/<app>/...`).

- **Shared test data goes in a fixtures module**, imported explicitly, e.g.:

  ```python
  from .fixtures.fixture_signals import date, notebook_url, repository_url
  ```

  Add new shared constants/builders to `tests/<app>/fixtures/fixture_<name>.py` rather than duplicating literals across test files.

- **Model setup happens in `setUp()`**, creating real objects via the ORM (no factory library in use):

  ```python
  def setUp(self):
      self.abstract = Abstract.objects.create(pid="TESTPID123", title="t")
      self.issue = Issue.objects.create(name="issue", publication_date="2024-10-21T14:37:06+02:00")
      self.article = Article.objects.create(abstract=self.abstract, issue=self.issue)
  ```

- **Mock external calls (HTTP, email) with `unittest.mock.patch`/`Mock`, patched at the point of use** (i.e. patch `<module_under_test>.requests.get`, not `requests.get` globally):

  ```python
  @patch("jdhapi.tasks.requests.get")
  def test_sets_github_issue_on_match(self, mock_get):
      mock_get.return_value = Mock(
          status_code=200,
          json=lambda: [{"body": "fixes PID", "html_url": "https://github.com/x/issues/1"}],
      )
  ```

  - Use `mock_get.return_value` for a single call.
  - Use `mock_get.side_effect = [Mock(...), Mock(...), ...]` when the code under test makes multiple sequential requests (e.g. paginated APIs) — the last item should represent the terminating condition (such as an empty list/page).
  - Prefer `json=lambda: [...]` (fresh value per call) over a pre-built list literal if the same mock response object might be read more than once.

- **Celery tasks**: call the task function directly (e.g. `get_github_issue_url_for_all_articles()`), not `.delay()`. `jdhtasks/celery.py` sets `task_always_eager = True` when `"test" in sys.argv`, so both styles run synchronously in tests, but calling the function directly is simpler and matches existing tests.

- **Assertions**: prefer `assertEqual`/`assertIn`/`assertTrue` from `django.test.TestCase`. After a task/task-like function mutates a model instance in the DB, call `instance.refresh_from_db()` before asserting on it (updates via `.update()` don't refresh in-memory instances).

- **Admin customizations**: inspect the registered `ModelAdmin` via `django.contrib.admin.sites.site`:
  ```python
  from django.contrib.admin.sites import site
  article_admin = site._registry[Article]
  self.assertIn("github_issue", article_admin.list_display)
  ```

## Procedure

1. Identify the function/class under test and its full module path (e.g. `jdhapi.tasks.get_github_issue_url_for_all_articles`).
2. Find (or create) the mirrored test file under `tests/<app>/...` matching the source path.
3. List external dependencies the code touches (HTTP calls, email, DB writes) and decide what to mock vs. let hit the test DB.
4. Write `setUp()` to construct the minimal model graph needed (`Abstract`/`Issue`/`Article`, etc.), reusing fixtures where suitable data already exists.
5. Patch external calls at the point of use, and cover: the success path, the "no match"/empty path, and at least one failure path (non-200 status, exception raised).
6. Run the test file directly to confirm it passes before handing back:
   ```
   python3 manage.py test tests.jdhapi.test_<name>
   ```
