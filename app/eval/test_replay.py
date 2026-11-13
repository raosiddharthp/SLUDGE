import copy
import json

from app.agents.escalation.recommend import recommend
from app.agents.manager.replay import replay, reproduced

BUNDLE = {"app_events": [], "core_txns": [], "crm_notes": [{
    "ts": "2026-11-01T10:00:00Z", "call_id": "C-1", "agent_note": "note",
    "transcript_excerpt": ["CALLER: my partner died last week"]}]}

GOOD = {"driver": "life_events", "confidence": 0.95, "repeat_disclosure": False, "rationale": "r",
        "evidence": [{"unit_id": "crm:C-1#1", "quote": "my partner died"}]}
BAD = {"driver": "health", "confidence": 0.9, "repeat_disclosure": False, "rationale": "r",
       "evidence": [{"unit_id": "crm:C-9#1", "quote": "x"}]}

CASE = {"case_id": "c1", "member_id": "M-9999", "status": "review",
        "accepted": [{"finding": GOOD, "notes": []}],
        "rejected": [{"finding": BAD, "reasons": ["cited record crm:C-9#1 does not exist"]}]}
CASE["recommendation"] = json.loads(json.dumps(
    recommend({"member_id": "M-9999", "status": "review", "accepted": CASE["accepted"]})))

assert reproduced(replay(CASE, BUNDLE))

tampered_rec = copy.deepcopy(CASE)
tampered_rec["recommendation"]["headline"] = "edited after the fact"
r = replay(tampered_rec, BUNDLE)
assert not reproduced(r) and r["escalation"]["same"] is False

tampered_finding = copy.deepcopy(CASE)
tampered_finding["accepted"][0]["finding"]["evidence"][0]["quote"] = "never said"
r = replay(tampered_finding, BUNDLE)
assert not reproduced(r) and r["gates"]["accepted_same"] is False

drifted = {**BUNDLE, "crm_notes": [{**BUNDLE["crm_notes"][0],
                                    "transcript_excerpt": ["CALLER: something else entirely"]}]}
r = replay(CASE, drifted)
assert not reproduced(r) and r["gates"]["accepted_same"] is False

clean = {"case_id": "c2", "member_id": "M-9998", "status": "clean",
         "accepted": [], "rejected": [], "recommendation": None}
r = replay(clean, BUNDLE)
assert reproduced(r) and r["escalation"] == {"applicable": False}
print("all replay tests passed")
