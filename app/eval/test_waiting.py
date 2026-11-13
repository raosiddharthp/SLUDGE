"""A newer decided or clean case hides an older pending one for the same member."""
from datetime import datetime, timezone

from app.agents.manager.queue import waiting


def case(cid, member, minute, state, status="review"):
    return {"case_id": cid, "member_id": member, "status": status, "review_state": state,
            "created_at": datetime(2026, 11, 13, 10, minute, tzinfo=timezone.utc),
            "recommendation": {"urgency": "normal", "headline": "h"}}


older = case("a", "M-1003", 1, "pending")
decided = case("b", "M-1003", 2, "decided")
other = case("c", "M-1002", 3, "pending")
clean = case("d", "M-1005", 4, "closed_clean", status="clean")
old_5 = case("e", "M-1005", 0, "pending")
newer = case("f", "M-1003", 5, "pending")

assert [r["case_id"] for r in waiting([older, decided, other, clean, old_5])] == ["c"]
assert [r["case_id"] for r in waiting([older, other])] == ["a", "c"]
assert [r["case_id"] for r in waiting([older, newer])] == ["f"]
print("all waiting tests passed")
