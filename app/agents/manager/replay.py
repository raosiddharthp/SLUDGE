"""Replay a stored case through the deterministic stages (gates, Escalation). No LLM, no cost."""
import json

from app.agents.escalation.recommend import recommend
from app.agents.manager.gates import review


def _findings(items):
    return [i["finding"] for i in items or []]


def _norm(value):
    return json.loads(json.dumps(value, default=str))


def replay_gates(case, bundle):
    """Feed the stored findings back through the gates. The stored accepted ones are already adjusted,
    and both adjustments are idempotent, so a faithful replay accepts and rejects the same findings."""
    stored = _findings(case.get("accepted")) + _findings(case.get("rejected"))
    accepted, rejected = review(bundle, stored)
    return {
        "accepted_same": _findings(accepted) == _findings(case.get("accepted")),
        "rejected_same": _findings(rejected) == _findings(case.get("rejected")),
        "reasons_same": [r["reasons"] for r in rejected]
                        == [r["reasons"] for r in case.get("rejected") or []],
    }


def replay_escalation(case):
    """Recompute the recommendation from exactly what Escalation was given and compare."""
    if case.get("status") != "review" or not case.get("accepted"):
        return {"applicable": False}
    given = {"member_id": case["member_id"], "status": case["status"], "accepted": case["accepted"]}
    return {"applicable": True, "same": _norm(recommend(given)) == _norm(case.get("recommendation"))}


def replay(case, bundle):
    return {"case_id": case["case_id"], "gates": replay_gates(case, bundle),
            "escalation": replay_escalation(case)}


def reproduced(result):
    esc = result["escalation"]
    return all(result["gates"].values()) and (not esc["applicable"] or esc["same"])
