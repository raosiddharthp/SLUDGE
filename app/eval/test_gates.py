"""Offline test of the grounding gates against Grace's seed records. No network."""
from app.agents.ingest.sources import fetch_bundle
from app.agents.manager.gates import review


def finding(driver, conf, units, repeat=False):
    return {
        "driver": driver, "confidence": conf, "repeat_disclosure": repeat, "rationale": "x",
        "evidence": [{"unit_id": u, "quote": q} for u, q in units],
    }


CASES = [
    finding("health", 0.95, [("crm:C-2006#1", "diagnosed with breast cancer")]),
    finding("resilience", 0.95, [("core:2026-03-12T00:00:00Z:PAYMENT_HOLIDAY_START", "PAYMENT_HOLIDAY_START")]),
    finding("health", 0.9, [("crm:C-2006#1", "diagnosed with leukaemia")]),
    finding("health", 0.9, [("crm:C-9999#1", "anything")]),
    finding("resilience", 0.7, [("crm:C-2007#note", "another payment holiday")], repeat=True),
    finding("health", 0.9, []),
]

accepted, rejected = review(fetch_bundle("M-1004"), CASES)
assert len(accepted) == 3 and len(rejected) == 3, (len(accepted), len(rejected))
assert accepted[0]["finding"]["confidence"] == 0.95 and not accepted[0]["notes"]
assert accepted[1]["finding"]["confidence"] == 0.8 and accepted[1]["notes"]
assert accepted[2]["finding"]["repeat_disclosure"] is False and accepted[2]["notes"]
for r in rejected:
    print("rejected:", r["reasons"][0])
for a in accepted:
    print("accepted:", a["finding"]["driver"], a["finding"]["confidence"], a["notes"])
print("all gate tests passed")
