#!/usr/bin/env python3
import logging
import os
import sys
import time
from datetime import datetime, timezone
import requests
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def trigger_workflow(repo_url, workflow_filename, token=None, ref="main"):
    """
    :param owner: GitHub username or organization
    :param repo: Repository name
    :param workflow_filename: Filename of the workflow in .github/workflows (e.g. "hello-world.yml")
    :param ref: Git ref (branch or tag) to run the workflow on
    """
    token = _get_github_token(token)
    owner, repo = _parse_owner_repo(repo_url)

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_filename}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"ref": ref}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 204:
            logger.info(
                "Workflow '%s' dispatched on ref '%s' for %s/%s.",
                workflow_filename,
                ref,
                owner,
                repo,
            )
            return

        logger.error(
            "Failed to dispatch workflow '%s' (%s): %s",
            workflow_filename,
            resp.status_code,
            resp.text,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Workflow dispatch failed: %s", e)
        raise


def trigger_workflow_and_wait(
    repo_url,
    workflow_filename,
    token=None,
    ref="main",
    timeout_seconds=600,
    poll_interval_seconds=5,
):
    token = _get_github_token(token)
    owner, repo = _parse_owner_repo(repo_url)
    started_at = datetime.now(timezone.utc)

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
            resp = requests.get(runs_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("Failed to list workflow runs: %s", e)
            raise

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
                        f"Workflow '{workflow_filename}' завершён: {conclusion}"
                    )
                break

        if run_id is None:
            logger.info("Waiting for workflow run to start...")

        time.sleep(poll_interval_seconds)

    raise TimeoutError(
        f"Workflow '{workflow_filename}' did not complete within {timeout_seconds}s"
    )


def _parse_owner_repo(repo_url):
    parsed = urlparse(repo_url)
    path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]

    raise ValueError(f"Invalid repository URL: '{repo_url}'")


def _get_github_token(token):
    if token:
        return token
    from jdh.settings import GITHUB_ACCESS_TOKEN

    return GITHUB_ACCESS_TOKEN


def _parse_github_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None