#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse


def trigger_workflow(repo_url, workflow_filename, token=None, ref="main"):
    """
    :param owner: GitHub username or organization
    :param repo: Repository name
    :param workflow_filename: Filename of the workflow in .github/workflows (e.g. "hello-world.yml")
    :param ref: Git ref (branch or tag) to run the workflow on
    """
    if not token:
        from jdh.settings import GITHUB_ACCESS_TOKEN

        token = GITHUB_ACCESS_TOKEN

    parsed = urlparse(repo_url)
    path = parsed.path.lstrip("/")

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1]

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_filename}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"ref": ref}
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 204:
        print(f"Workflow '{workflow_filename}' dispatched on ref '{ref}'.")
    else:
        print(f"Failed to dispatch workflow: {resp.status_code}")
        print(resp.json())
        resp.raise_for_status()
