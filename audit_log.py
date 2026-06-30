"""
Audit log: an append-only, file-backed structured log.

Entry schema (per spec):
    {
        "content_id": str,
        "creator_id": str,
        "timestamp": str (ISO 8601, UTC, e.g. "2025-04-01T14:32:10.123Z"),
        "attribution": str,            # "likely_ai" | "uncertain" | "likely_human" (code)
        "transparency_label": str,     # user-facing label text, per spec wording
        "confidence": float,           # combined majority-vote confidence (0.0/0.5/1.0)
        "llm_score": float,            # signal 1's self-reported confidence (0-1)
        "stylometric_score": float,    # signal 2's combined heuristic score (0-1)
        "votes": dict,                 # each signal's individual binary vote
        "status": str,                 # "classified" | "under_review" | ...
        "appeal_filed": bool,           # explicit flag, set True on appeal
        "appeal_reasoning": str|None,  # creator's reasoning, set on appeal
        "appealed_at": str|None,       # timestamp of appeal, set on appeal
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
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    # Guard against stale/incompatible formats (e.g. an old dict-keyed
    # version of this file) rather than crashing or silently misreading it.
    if not isinstance(data, list):
        return []
    return data


def _save(entries):
    with open(_LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def _utc_timestamp():
    """e.g. '2025-04-01T14:32:10.123Z' — millisecond precision, UTC, Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def create_entry(content_id, creator_id, text, attribution, transparency_label,
                  confidence, llm_score, stylometric_score, votes, status="classified"):
    """Append one structured entry to the audit log. Returns the entry."""
    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": _utc_timestamp(),
        "attribution": attribution,
        "transparency_label": transparency_label,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylometric_score": stylometric_score,
        "votes": votes,
        "status": status,
        "appeal_filed": False,
        "appeal_reasoning": None,
        "appealed_at": None,
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


def file_appeal(content_id, appeal_reasoning, status="under_review"):
    """
    Record an appeal against an existing submission, in place.

    Sets status (default "under_review"), appeal_reasoning, and
    appealed_at on the existing entry — alongside (not replacing) the
    original classification decision already stored there.

    Returns the updated entry, or None if content_id isn't found.
    """
    with _LOCK:
        entries = _load()
        for entry in entries:
            if entry["content_id"] == content_id:
                entry["status"] = status
                entry["appeal_filed"] = True
                entry["appeal_reasoning"] = appeal_reasoning
                entry["appealed_at"] = _utc_timestamp()
                _save(entries)
                return entry
    return None


def get_log(limit=20):
    """Return the most recent `limit` entries, newest first."""
    with _LOCK:
        entries = _load()
    return list(reversed(entries))[:limit]