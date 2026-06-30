"""
Audit log: an append-only, file-backed structured log.

Every call to /submit writes one entry here. Per the architecture diagram,
the Appeal flow (Milestone 5) will also write status updates into this same
log. Using a JSON file (rather than print statements or an in-memory dict)
so entries are structured, inspectable, and survive server restarts.

Entry schema (per spec):
    {
        "content_id": str,
        "creator_id": str,
        "timestamp": str (ISO 8601, UTC, e.g. "2025-04-01T14:32:10.123Z"),
        "attribution": str,      # e.g. "likely_ai" / "likely_human"
        "confidence": float,     # overall confidence (placeholder until
                                  # majority-vote scoring exists — Milestone 4)
        "llm_score": float,      # signal 1's own self-reported confidence
        "status": str,           # "classified" | "appealed" | "resolved" ...
    }

Plus one extra field not in the spec's example but needed for the Appeal
flow later: "text" (the original submitted content), so an appeal can be
matched back against what was actually assessed.

If this needs to support concurrent writers or higher volume later, swap
the storage layer for SQLite behind the same function signatures — the
calling code (app.py) wouldn't need to change.
"""

import json
import os
import threading
from datetime import datetime, timezone

_LOCK = threading.Lock()
_LOG_PATH = os.path.join(os.path.dirname(__file__), "audit_log.json")


def _load():
    if not os.path.exists(_LOG_PATH):
        return []
    with open(_LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(entries):
    with open(_LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def _utc_timestamp():
    """e.g. '2025-04-01T14:32:10.123Z' — millisecond precision, UTC, Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def create_entry(content_id, creator_id, text, attribution, confidence, llm_score, status="classified"):
    """Append one structured entry to the audit log. Returns the entry."""
    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": _utc_timestamp(),
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "status": status,
        "text": text,
    }
    with _LOCK:
        entries = _load()
        entries.append(entry)
        _save(entries)
    return entry


def get_entry(content_id):
    """Fetch the most recent entry for a given content_id, or None."""
    with _LOCK:
        entries = _load()
    for entry in reversed(entries):
        if entry["content_id"] == content_id:
            return entry
    return None


def update_status(content_id, status, appeal_info=None):
    """Update the status (and optional appeal info) of an entry in place.

    Used by the Appeal flow (Milestone 5). Returns the updated entry, or
    None if content_id isn't found.
    """
    with _LOCK:
        entries = _load()
        for entry in entries:
            if entry["content_id"] == content_id:
                entry["status"] = status
                if appeal_info is not None:
                    entry["appeal"] = appeal_info
                _save(entries)
                return entry
    return None


def get_log(limit=20):
    """Return the most recent `limit` entries, newest first."""
    with _LOCK:
        entries = _load()
    return list(reversed(entries))[:limit]