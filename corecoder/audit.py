"""Append-only audit logging for tool activity."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_AUDIT_LOG = Path.home() / ".corecoder" / "audit.jsonl"


def write_audit_event(
    event: dict,
    log_path: Path | None = None,
) -> None:
    """Append one structured event to a JSONL audit log."""
    target = log_path or DEFAULT_AUDIT_LOG
    target.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
