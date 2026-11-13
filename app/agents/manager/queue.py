"""Read model for the reviewer screen: what is waiting, most urgent first."""
from google.cloud.firestore_v1.base_query import FieldFilter

from app.agents.manager.metrics import override_rate
from app.agents.manager.store import COLLECTION, _db

RANK = {"high": 0, "normal": 1}


def urgency(case):
    rec = case.get("recommendation")
    if rec:
        return rec["urgency"]
    # No recommendation: a failed or unrecommended case needs a person quickly.
    return "high" if case["status"] == "queued_error" or case.get("accepted") else "normal"


def headline(case):
    rec = case.get("recommendation")
    if rec:
        return rec["headline"]
    if case["status"] == "queued_error":
        return f"Assessment failed at {case.get('stage')}: needs manual review"
    if case.get("accepted"):
        return "Findings verified but no recommendation was produced"
    return "Model output was rejected by the grounding gates"


def latest_per_member(cases):
    """Each member's newest case, whatever state it is in."""
    latest = {}
    for c in cases:
        m = c["member_id"]
        if m not in latest or c["created_at"] > latest[m]["created_at"]:
            latest[m] = c
    return list(latest.values())


def build_queue(cases):
    """Latest case per member, urgent first, oldest first within an urgency."""
    rows = [{"case_id": c["case_id"], "member_id": c["member_id"], "status": c["status"],
             "urgency": urgency(c), "headline": headline(c), "created_at": c["created_at"]}
            for c in latest_per_member(cases)]
    return sorted(rows, key=lambda r: (RANK[r["urgency"]], r["created_at"]))


def waiting(cases):
    """What a person still has to review: a member's newest case, if it is pending.

    An older pending case never resurfaces once a newer case exists for the same member."""
    return build_queue([c for c in latest_per_member(cases) if c.get("review_state") == "pending"])


def pending_queue():
    return waiting([d.to_dict() for d in _db().collection(COLLECTION).stream()])


def override_stats():
    q = _db().collection(COLLECTION).where(filter=FieldFilter("review_state", "==", "decided"))
    return override_rate([d.to_dict() for d in q.stream()])
