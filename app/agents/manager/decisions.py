"""Reviewer decisions on pending cases. Pure rules first; one Firestore transaction applies them."""
from datetime import datetime, timezone

from google.cloud import firestore

from app.agents.manager.store import COLLECTION, _db

CHOICES = {"confirm", "dismiss"}


def apply_decisions(case, decisions, reviewer, note=""):
    """Validate a reviewer's decisions against a case and return the fields to write."""
    if case.get("review_state") != "pending":
        raise ValueError(f"case is {case.get('review_state')}, not pending")
    if not (reviewer or "").strip():
        raise ValueError("reviewer is required")
    note = (note or "").strip()
    accepted = case.get("accepted") or []
    decisions = {int(k): v for k, v in (decisions or {}).items()}

    if not accepted:
        if decisions:
            raise ValueError("this case has no findings to decide")
        if not note:
            raise ValueError("note is required: say how this case was handled")
        outcome = "manual" if case["status"] == "queued_error" else "acknowledged"
        rows = []
    else:
        if set(decisions) != set(range(len(accepted))):
            raise ValueError(f"decide every finding: expected indexes 0..{len(accepted) - 1}")
        if not set(decisions.values()) <= CHOICES:
            raise ValueError("each decision must be 'confirm' or 'dismiss'")
        if "dismiss" in decisions.values() and not note:
            raise ValueError("note is required when dismissing a finding")
        rows = [{"index": i, "driver": accepted[i]["finding"]["driver"], "decision": decisions[i]}
                for i in sorted(decisions)]
        kinds = set(decisions.values())
        outcome = "confirmed" if kinds == {"confirm"} else "dismissed" if kinds == {"dismiss"} else "partial"

    return {
        "decisions": rows,
        "outcome": outcome,
        "reviewer": reviewer.strip(),
        "review_note": note,
        "review_state": "decided",
        "decided_at": datetime.now(timezone.utc),
    }


@firestore.transactional
def _apply(tx, ref, decisions, reviewer, note):
    snap = ref.get(transaction=tx)
    if not snap.exists:
        raise KeyError("no such case")
    update = apply_decisions(snap.to_dict(), decisions, reviewer, note)
    tx.update(ref, update)
    return update


def decide_case(case_id, decisions, reviewer, note=""):
    """Record a reviewer's decisions on a pending case, atomically. Returns what was written."""
    ref = _db().collection(COLLECTION).document(case_id)
    return _apply(_db().transaction(), ref, decisions, reviewer, note)
