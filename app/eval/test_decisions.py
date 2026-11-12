"""Offline test of the reviewer decision rules. No network."""
from app.agents.manager.decisions import apply_decisions


def case(n_findings, status="review", state="pending"):
    accepted = [{"finding": {"driver": d}, "notes": []} for d in ["health", "resilience"][:n_findings]]
    return {"status": status, "review_state": state, "accepted": accepted}


def fails(*args):
    try:
        apply_decisions(*args)
    except ValueError:
        return True
    return False


assert apply_decisions(case(2), {0: "confirm", 1: "dismiss"}, "rev", "not supported")["outcome"] == "partial"
assert apply_decisions(case(1), {"0": "confirm"}, "rev")["outcome"] == "confirmed"
assert apply_decisions(case(2), {0: "dismiss", 1: "dismiss"}, "rev", "no evidence")["outcome"] == "dismissed"
assert fails(case(2), {0: "confirm"}, "rev")                       # skipped a finding
assert fails(case(2), {0: "confirm", 1: "dismiss"}, "rev", "")     # dismissal needs a note
assert fails(case(1), {0: "maybe"}, "rev")                         # invalid choice
assert fails(case(1), {0: "confirm", 5: "confirm"}, "rev")         # unknown index
assert fails(case(1), {0: "confirm"}, "  ")                        # reviewer required
assert fails(case(1, state="decided"), {0: "confirm"}, "rev")      # already decided
assert fails(case(1, state="closed_clean"), {0: "confirm"}, "rev") # clean cases are not reviewed
assert fails(case(0, status="queued_error"), {}, "rev", "")        # failed case needs a note
assert apply_decisions(case(0, status="queued_error"), {}, "rev", "assessed by phone")["outcome"] == "manual"
assert apply_decisions(case(0), {}, "rev", "model fabricated a quote")["outcome"] == "acknowledged"
print("all decision tests passed")
