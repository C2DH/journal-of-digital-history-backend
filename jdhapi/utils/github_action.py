#!/usr/bin/env python3
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from jdh.settings import GITHUB_ACCESS_TOKEN

logger = logging.getLogger(__name__)


def trigger_workflow(repo_url, workflow_filename, token=None, ref="main"):
    """
    :param repo_url: GitHub repository link
    :param workflow_filename: Filename of the workflow in .github/workflows (e.g. "hello-world.yml")
    :param token: GitHub access token with repo permissions (optional, will use env variable if not provided)
    :param ref: Git ref (branch or tag) to run the workflow on
    """
    token = _get_github_token(token)
    owner, repo = _parse_owner_repo(repo_url)

    logger.info(
        "[trigger_workflow] - Trigger workflow '%s' on ref '%s' for %s/%s",
        workflow_filename,
        ref,
        owner,
        repo,
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_filename}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"ref": ref}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 204:
            logger.info(
                "Workflow '%s' dispatched on ref '%s' for %s/%s.",
                workflow_filename,
                ref,
                owner,
                repo,
            )
        else:
            logger.error(
                "Failed to dispatch workflow '%s' (%s): %s",
                workflow_filename,
                res.status_code,
                res.text,
            )
        res.raise_for_status()
    except requests.RequestException as e:
        logger.error("Workflow dispatch failed: %s", e)
        raise requests.RequestException(f"Workflow dispatch failed: {e}") from e


def trigger_workflow_and_wait(
    repo_url,
    workflow_filename,
    token=None,
    ref="main",
    timeout_seconds=600,
    poll_interval_seconds=5,
):
    """
    :param repo_url: GitHub repository link
    :param workflow_filename: Filename of the workflow in .github/workflows (e.g. "hello-world.yml")
    :param token: GitHub access token with repo permissions (optional, will use env variable if not provided)
    :param ref: Git ref (branch or tag) to run the workflow on
    :param timeout_seconds: Maximum time to wait for workflow completion
    :param poll_interval_seconds: Time to wait between polling for workflow status
    """

    token = _get_github_token(token)
    owner, repo = _parse_owner_repo(repo_url)
    started_at = datetime.now(timezone.utc)

    logger.info(
        "[trigger_workflow_and_wait] - Trigger workflow and wait for '%s' on ref '%s' for %s/%s",
        workflow_filename,
        ref,
        owner,
        repo,
    )

    trigger_workflow(repo_url, workflow_filename, token=token, ref=ref)

    runs_url = (
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/"
        f"{workflow_filename}/runs"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    deadline = time.time() + timeout_seconds
    run_id = None

    while time.time() < deadline:
        try:
            res = requests.get(runs_url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
        except requests.RequestException as e:
            logger.error("Failed to list workflow runs: %s", e)
            raise requests.RequestException(f"Workflow dispatch failed: {e}") from e

        for run in data.get("workflow_runs", []):
            created_at = _parse_github_datetime(run.get("created_at"))
            if not created_at:
                continue
            if (
                run.get("event") == "workflow_dispatch"
                and run.get("head_branch") == ref
                and created_at >= started_at
            ):
                run_id = run.get("id")
                status = run.get("status")
                conclusion = run.get("conclusion")

                if status == "completed":
                    if conclusion == "success":
                        logger.info(
                            "Workflow '%s' completed successfully for %s/%s.",
                            workflow_filename,
                            owner,
                            repo,
                        )
                        return
                    raise RuntimeError(
                        f"Workflow '{workflow_filename}' interrupted: {conclusion}"
                    )
                break

        if run_id is None:
            logger.info("Waiting for workflow run to start...")

        time.sleep(poll_interval_seconds)

    raise TimeoutError(
        f"Workflow '{workflow_filename}' did not complete within {timeout_seconds}s"
    )


def _parse_owner_repo(repo_url):
    """
    Retrieve owner and repository name from a github repository url

    :param repo_url: Description
    :return: Return a tuple of (owner name, repository name)
    """
    logger.info(
        "[_parse_owner_repo] - Retrieve owner and repository name from a github repository url"
    )

    parsed = urlparse(repo_url)
    path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")

    owner = parts[0]
    repo = parts[1]

    if len(parts) >= 2:
        return owner, repo
    else:
        raise ValueError(f"Invalid repository URL: '{repo_url}'")


def _get_github_token(token):
    """
    Return the provided GitHub access token or fall back to the environment variable.

    :param token: GitHub access token (optional)
    :return: GitHub access token
    :raises ValueError: If no token is provided and none is set in the environment
    """
    logger.info("[_get_github_token] - Retrieve github access token")

    resolved = token or GITHUB_ACCESS_TOKEN
    if not resolved:
        raise ValueError(
            "No GitHub access token provided and GITHUB_ACCESS_TOKEN is not set."
        )
    return resolved


def _parse_github_datetime(value):
    """
    Parse a GitHub datetime string into a timezone-aware datetime object.
    GitHub datetime strings are in ISO 8601 format: "YYYY-MM-DDTHH:MM:SSZ"

    :param value: GitHub datetime string
    :return: Timezone-aware datetime object or None if parsing fails
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.error("Failed to parse GitHub datetime value: '%s'", value)
        return None
