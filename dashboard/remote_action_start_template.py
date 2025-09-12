#!/usr/bin/env python3
import os
import sys
import requests

def trigger_workflow(token, owner, repo, workflow_filename, ref="main"):
    """
    :param owner: GitHub username or organization
    :param repo: Repository name
    :param workflow_filename: Filename of the workflow in .github/workflows (e.g. "hello-world.yml")
    :param ref: Git ref (branch or tag) to run the workflow on
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_filename}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "ref": ref
        # "inputs": { "foo": "bar" }
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 204:
        print(f"Workflow '{workflow_filename}' dispatched on ref '{ref}'.")
    else:
        print(f"Failed to dispatch workflow: {resp.status_code}")
        print(resp.json())
        resp.raise_for_status()

if __name__ == "__main__":
    # token = os.getenv("GITHUB_TOKEN")
    token = "github_pat_*TOKEN-HERE*"
    if not token:
        print("Error: Please set the GITHUB_TOKEN environment variable and try again.")
        sys.exit(1)

    # Usage: python trigger.py <owner> <repo> <workflow-file> [ref]
    if len(sys.argv) < 4:
        print("Usage: python trigger.py <owner> <repo> <workflow-file.yml> [ref]")
        sys.exit(1)

    owner, repo, workflow_file = sys.argv[1:4]
    ref = sys.argv[4] if len(sys.argv) > 4 else "main"
    trigger_workflow(token, owner, repo, workflow_file, ref)
