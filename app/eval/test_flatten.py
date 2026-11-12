"""Offline test of the Firestore-to-BigQuery flattening. No network."""
from datetime import datetime, timezone

from app.agents.governance.flatten import case_row, finding_rows

T = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)


def finding(driver, repeat=False):
    return {"driver": driver, "confidence": 0.9, "repeat_disclosure": repeat,
            "evidence": [{"unit_id": "crm:C-1#1", "quote": "x"}]}


grace = {
    "case_id": "g1", "member_id": "M-1004", "status": "review", "review_state": "decided",
    "outcome": "partial", "model": "m", "tokens": {"in": 973, "out": 201}, "trail": ["detection attempt 1"],
    "accepted": [{"finding": finding("health", True), "notes": []},
                 {"finding": finding("resilience"), "notes": ["confidence capped"]}],
    "rejected": [{"finding": finding("capability"), "reasons": ["quote not found"]}],
    "recommendation": {"urgency": "high", "headline": "h"},
    "decisions": [{"index": 0, "driver": "health", "decision": "confirm"},
                  {"index": 1, "driver": "resilience", "decision": "dismiss"}],
    "created_at": T, "decided_at": T, "reviewer": "rev", "lawful_basis": "x", "retain_until": T,
}
sam = {"case_id": "s1", "member_id": "M-1005", "status": "clean", "review_state": "closed_clean",
       "tokens": {"in": 811, "out": 27}, "trail": [], "accepted": [], "rejected": [], "created_at": T}

row = case_row(grace)
assert row["accepted_n"] == 2 and row["rejected_n"] == 1 and row["failed_attempts"] == 1
assert row["tokens_in"] == 973 and row["urgency"] == "high" and row["created_at"] == T.isoformat()
rows = finding_rows(grace)
assert [(r["driver"], r["grounded"], r["decision"]) for r in rows] == [
    ("health", True, "confirm"), ("resilience", True, "dismiss"), ("capability", False, None)]
assert rows[0]["repeat_disclosure"] is True and rows[1]["adjusted"] is True
srow = case_row(sam)
assert srow["accepted_n"] == 0 and srow["urgency"] is None and srow["decided_at"] is None
assert finding_rows(sam) == []
print("all flatten tests passed")
