"""Deciding saves first, then asks Governance to catch up; a sync problem never loses the decision."""
from app.web import data

calls = []
data.decide_case = lambda *a: calls.append("decide") or {"outcome": "confirmed", "review_state": "decided"}


async def fake_notify(url, call, timeout=25):
    calls.append(("sync", url, timeout))
    return "synced"


data.notify_governance = fake_notify
data.GOVERNANCE_URL = "https://gov.example"
out = data.decide("case-1", [], "reviewer", "note")
assert calls == ["decide", ("sync", "https://gov.example", data.SYNC_WAIT)], calls
assert out == {"outcome": "confirmed", "review_state": "decided", "governance": "synced"}, out


async def failing_notify(url, call, timeout=25):
    return "skipped: TimeoutError"


data.notify_governance = failing_notify
out = data.decide("case-1", [], "reviewer", "note")
assert out["review_state"] == "decided" and out["governance"].startswith("skipped"), out
print("all decide-sync tests passed")
