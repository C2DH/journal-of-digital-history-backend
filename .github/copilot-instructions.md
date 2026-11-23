When performing a code review, respond in English.

When performing a code review, give your comments as simple as possible.

When performing a code review, focus on readability and avoid nested ternary operators.

When performing a code review, try to apply good practice in code as much as possible.

When performing a code review, reference the exact line and suggest a short fix.

When performing a code review, prefer early returns over deep nesting.

When performing a code review, check that functions are small and have a single responsibility.

When performing a code review, check that new functions have type hints.

When performing a code review, flag `print` statements and suggest `logging` instead.

When performing a code review, flag bare `except:` and swallowed exceptions.

When performing a code review, check that business logic is kept out of views and serializers.

When performing a code review, check that every new endpoint has authentication and permissions.

When performing a code review, check that multi-step writes use `transaction.atomic`.

When performing a code review, check that Celery tasks in `jdhtasks` are idempotent and receive simple serializable arguments (IDs, not model instances).

When performing a code review, check that external calls in Celery tasks handle timeouts, retries, and errors.

When performing a code review, flag any secret, token, or credential in code and suggest environment variables instead (see `.env.example`).

When performing a code review, check that new dependencies are pinned and justified.

When performing a code review, check that new behavior and bug fixes have tests in `tests/`, cover edge cases, and mock external services.

When performing a code review, flag breaking API changes (renamed fields, removed endpoints), because the frontend consumes this API.
