"""Offline test of the reviewer queue rules. No network."""
from app.agents.manager.queue import build_queue


def case(cid, member, created, status="review", rec=None, accepted=True, stage=None):
    return {"case_id": cid, "member_id": member, "created_at": created, "status": status,
            "recommendation": rec, "accepted": [{}] if accepted else [], "stage": stage}


def rec(urgency, headline="Possible vulnerability: x"):
    return {"urgency": urgency, "headline": headline}


rows = build_queue([
    case("grace-old", "M-1004", 1, rec=rec("high")),
    case("percy", "M-1002", 2, rec=rec("normal")),
    case("grace-new", "M-1004", 3, rec=rec("high")),
    case("failed", "M-1009", 4, status="queued_error", accepted=False, stage="detection"),
    case("rejected", "M-1010", 5, accepted=False),
    case("no-rec", "M-1011", 6),
])
order = [r["case_id"] for r in rows]
assert order == ["grace-new", "failed", "no-rec", "percy", "rejected"], order
assert "grace-old" not in order                      # superseded by the latest case for that member
assert rows[1]["headline"].startswith("Assessment failed at detection")
assert rows[2]["headline"].startswith("Findings verified")
assert rows[4]["headline"].startswith("Model output was rejected")
print(order)
print("all queue tests passed")
