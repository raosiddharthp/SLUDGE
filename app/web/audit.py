"""Access log: who looked at which case. Feeds the Redact lens. No IP address or identity is stored."""
from datetime import datetime, timedelta, timezone

COLLECTION = "sludge_access_log"
ACTOR = "public-demo"


def entry(case_id, member_id, now=None, retention_days=90):
    """One document per case per minute, so refreshing a page cannot flood the log."""
    now = now or datetime.now(timezone.utc)
    return f"{case_id}-{now.strftime('%Y%m%dT%H%M')}", {
        "case_id": case_id, "member_id": member_id, "actor": ACTOR, "action": "view_case",
        "at": now, "retain_until": now + timedelta(days=retention_days),
    }


def record(db, case_id, member_id, retention_days=90, now=None):
    doc_id, doc = entry(case_id, member_id, now, retention_days)
    db.collection(COLLECTION).document(doc_id).set(doc)
