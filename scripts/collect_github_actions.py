"""Collect real GitHub Actions jobs as provenance-preserving JSONL records.

Use a fine-grained token in GITHUB_TOKEN for private repositories.  The token
needs Actions read access only; it is never written to the dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


EMAIL = re.compile(r"(?i)\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b")
IPV4 = re.compile(r"\\b(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)(?:\\.(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)){3}\\b")
TOKEN = re.compile(r"(?i)\\b(?:ghp|github_pat|glpat|xox[baprs])-?[A-Za-z0-9_=-]{16,}\\b")


def redact(value: str) -> str:
    return TOKEN.sub("<TOKEN>", IPV4.sub("<IPV4>", EMAIL.sub("<EMAIL>", value)))


def request(url: str, token: str | None, accept: str = "application/vnd.github+json") -> bytes:
    headers = {"Accept": accept, "User-Agent": "Agent_Dev_Ops-data-collector"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read()


def api_json(url: str, token: str | None) -> dict[str, Any]:
    return json.loads(request(url, token).decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/repository")
    parser.add_argument("--out", default="data/processed/cicd_v1.0.jsonl")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "GITHUB_TOKEN est requis pour télécharger les logs GitHub Actions. "
            "Utilisez un token fine-grained avec Actions: read."
        )
    base = f"https://api.github.com/repos/{args.repo}"
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if output.exists():
        for line in output.read_text(encoding="utf-8").splitlines():
            existing.add(json.loads(line)["incident_id"])

    runs = api_json(f"{base}/actions/runs?per_page={args.limit}", token)["workflow_runs"]
    inserted = 0
    with output.open("a", encoding="utf-8", newline="\n") as sink:
        for run in runs:
            jobs = api_json(f"{base}/actions/runs/{run['id']}/jobs?per_page=100", token)["jobs"]
            for job in jobs:
                incident_id = hashlib.sha256(
                    f"github-actions:{args.repo}:{run['id']}:{job['id']}".encode()
                ).hexdigest()
                if incident_id in existing:
                    continue
                # GitHub returns a temporary redirect to the decoded text archive.
                # Its Actions endpoint rejects an octet-stream Accept header.
                raw_log = request(f"{base}/actions/jobs/{job['id']}/logs", token)
                record = {
                    "incident_id": incident_id,
                    "provider": "github_actions",
                    "repository": args.repo,
                    "workflow_run_id": run["id"],
                    "workflow_name": run["name"],
                    "head_sha": run["head_sha"],
                    "run_url": run["html_url"],
                    "job_id": job["id"],
                    "job_name": job["name"],
                    "status": job["status"],
                    "conclusion": job["conclusion"],
                    "failed_step": next((step["name"] for step in job.get("steps", []) if step.get("conclusion") == "failure"), None),
                    "log_message": redact(raw_log.decode("utf-8", errors="replace")),
                    "failure_category": None,
                    "root_cause": None,
                    "proposed_remediation": None,
                    "label_status": "unlabeled",
                    "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                inserted += 1
    print(json.dumps({"inserted": inserted, "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
