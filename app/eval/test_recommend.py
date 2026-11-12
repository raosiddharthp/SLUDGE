"""Offline test of the Escalation rules, using the real Grace case from the cloud run."""
from app.agents.escalation.recommend import recommend


def finding(driver, repeat=False, quote="I can't work."):
    return {"finding": {"driver": driver, "confidence": 0.95, "repeat_disclosure": repeat,
                        "evidence": [{"unit_id": "crm:C-1#1", "quote": quote}]}, "notes": []}


def fails(case):
    try:
        recommend(case)
    except ValueError:
        return True
    return False


grace = {"member_id": "M-1004", "status": "review",
         "accepted": [finding("health"), finding("resilience", repeat=True, quote="I'm not doing this again.")]}
r = recommend(grace)
assert r["urgency"] == "high" and r["requires"] == "human_decision"
assert "health condition" in r["headline"] and "repeat themselves" in r["headline"]
assert [a["action"] for a in r["actions"]] == ["offer_support", "review_affordability", "record_once"]
assert r["actions"][2]["findings"] == [1]
assert [e["quote"] for e in r["evidence"]] == ["I can't work.", "I'm not doing this again."]

calm = recommend({"member_id": "M-1003", "status": "review", "accepted": [finding("capability")]})
assert calm["urgency"] == "normal" and [a["action"] for a in calm["actions"]] == ["adapt_communication"]

assert fails({"status": "clean", "accepted": []})
assert fails({"status": "queued_error"})
assert fails({"status": "review", "accepted": []})
bad = finding("health"); bad["finding"]["evidence"] = []
assert fails({"status": "review", "accepted": [bad]})
assert fails({"status": "review", "accepted": [finding("other")]})
print(r["headline"])
print("all recommendation tests passed")
