"""Append-only JSONL audit log of trigger events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append(audit_path: Path, event: dict[str, Any]) -> None:
    """Append a JSON event to `audit_path`. Creates the file/dir if missing.

    A `ts` field is added with the current UTC ISO-8601 timestamp.
    """
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
