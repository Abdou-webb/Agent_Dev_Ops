"""Validate the versioned Agent_Dev_Ops dataset without third-party packages."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "processed" / "observability_v0.1.jsonl"
MANIFEST = ROOT / "data" / "processed" / "manifest.json"
REQUIRED = {
    "record_id", "source", "source_dataset", "source_url", "source_line_id",
    "event_template", "log_message", "native_label", "failure_category",
    "root_cause", "remediation", "label_status",
}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    record_ids: set[str] = set()
    with DATASET.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            record = json.loads(line)
            missing = REQUIRED - record.keys()
            if missing:
                raise ValueError(f"ligne {number}: champs manquants {sorted(missing)}")
            if record["record_id"] in record_ids:
                raise ValueError(f"ligne {number}: record_id dupliqué")
            record_ids.add(record["record_id"])
            counts[record["source_dataset"]] += 1
    if len(record_ids) != manifest["records"]:
        raise ValueError("nombre de lignes différent du manifeste")
    if sum(source["records"] for source in manifest["sources"]) != len(record_ids):
        raise ValueError("comptage des sources différent du manifeste")
    print(json.dumps({"records": len(record_ids), "by_source": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
