"""Daily assessment cap: a pure rule plus a Firestore transaction so concurrent callers cannot overshoot."""
import os
from datetime import datetime, timezone

from google.cloud import firestore

COLLECTION = "sludge_usage"
DEFAULT_CAP = 20


def day_key(now=None):
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")


def limit():
    """Cap from SLUDGE_DAILY_CAP; a missing, invalid or negative value falls back to the default."""
    try:
        value = int(os.environ.get("SLUDGE_DAILY_CAP", DEFAULT_CAP))
    except ValueError:
        return DEFAULT_CAP
    return value if value >= 0 else DEFAULT_CAP


def next_count(used, cap):
    """Pure rule: returns (allowed, new_used). A denied call does not consume a slot."""
    if used >= cap:
        return False, used
    return True, used + 1


@firestore.transactional
def _take(txn, ref, cap):
    snap = ref.get(transaction=txn)
    used = (snap.to_dict() or {}).get("count", 0) if snap.exists else 0
    allowed, new = next_count(used, cap)
    if allowed:
        txn.set(ref, {"count": new, "cap": cap, "day": ref.id})
    return {"allowed": allowed, "used": new, "cap": cap, "remaining": max(cap - new, 0)}


def take(db, cap=None, now=None):
    """Try to take one slot for today (UTC). db is a Firestore client."""
    cap = limit() if cap is None else cap
    return _take(db.transaction(), db.collection(COLLECTION).document(day_key(now)), cap)


def peek(db, cap=None, now=None):
    """Today's usage without taking a slot."""
    cap = limit() if cap is None else cap
    snap = db.collection(COLLECTION).document(day_key(now)).get()
    used = (snap.to_dict() or {}).get("count", 0) if snap.exists else 0
    return {"used": used, "cap": cap, "remaining": max(cap - used, 0)}
