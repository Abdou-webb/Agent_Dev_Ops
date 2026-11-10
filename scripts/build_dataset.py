"""Build the first real, provenance-preserving Agent_Dev_Ops dataset.

Inputs are the public Loghub sample CSV files cloned under sources/loghub.
No synthetic log event or diagnostic label is created by this script.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources" / "loghub"
OUT = ROOT / "data" / "processed"
SETS = ("BGL", "HDFS", "Linux", "OpenStack", "Spark", "Zookeeper")

EMAIL = re.compile(r"(?i)\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b")
IPV4 = re.compile(r"\\b(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)(?:\\.(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)){3}\\b")
TOKEN = re.compile(r"(?i)\\b(?:ghp|github_pat|glpat|xox[baprs])-?[A-Za-z0-9_=-]{16,}\\b")


def redact(text: str) -> str:
    """Redact common personal/network/credential patterns conservatively."""
    text = EMAIL.sub("<EMAIL>", text)
    text = IPV4.sub("<IPV4>", text)
    return TOKEN.sub("<TOKEN>", text)


def source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "observability_v0.1.jsonl"
    manifest_rows = []
    counts = Counter()
    total = 0

    with output.open("w", encoding="utf-8", newline="\n") as sink:
        for dataset in SETS:
            path = SOURCE / dataset / f"{dataset}_2k.log_structured.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            source_url = (
                "https://github.com/logpai/loghub/blob/master/"
                f"{dataset}/{dataset}_2k.log_structured.csv"
            )
            row_count = 0
            with path.open("r", encoding="utf-8", newline="") as handle:
                for raw in csv.DictReader(handle):
                    # Native source labels are retained exactly; no missing label is inferred.
                    native_label = raw.get("Label") or None
                    record = {
                        "record_id": f"loghub-{dataset.lower()}-{raw['LineId']}",
                        "source": "Loghub",
                        "source_dataset": dataset,
                        "source_url": source_url,
                        "source_line_id": int(raw["LineId"]),
                        "timestamp_raw": raw.get("Timestamp") or None,
                        "date_raw": raw.get("Date") or None,
                        "time_raw": raw.get("Time") or None,
                        "component": raw.get("Component") or None,
                        "level": raw.get("Level") or None,
                        "node": raw.get("Node") or raw.get("NodeRepeat") or None,
                        "event_id": raw.get("EventId") or None,
                        "event_template": redact(raw.get("EventTemplate") or ""),
                        "log_message": redact(raw.get("Content") or ""),
                        "native_label": native_label,
                        "failure_category": None,
                        "root_cause": None,
                        "remediation": None,
                        "label_status": "native" if native_label is not None else "unlabeled",
                    }
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    row_count += 1
                    total += 1
                    counts[dataset] += 1
            manifest_rows.append({
                "source_dataset": dataset,
                "file": str(path.relative_to(ROOT)).replace("\\\\", "/"),
                "source_url": source_url,
                "sha256": source_sha(path),
                "records": row_count,
                "license": "Loghub research/academic license; attribution required",
            })

    manifest = {
        "dataset": "Agent_Dev_Ops observability v0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": total,
        "format": "JSONL; one real source log event per row",
        "sources": manifest_rows,
        "transformations": [
            "Copied selected source fields into a canonical schema",
            "Redacted e-mail addresses, IPv4 addresses, and token-shaped strings",
            "Preserved native labels without inferring incident categories",
        ],
        "not_suitable_for": [
            "Ground-truth CI/CD remediation training",
            "Automatic deployment or rollback decisions",
        ],
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"records": total, "by_source": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
