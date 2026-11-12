"""Offline test: Manager -> Escalation wiring (gate 3) and the override-rate metric."""
import asyncio
import json

from app.agents.escalation.recommend import recommend
from app.agents.ingest.sources import fetch_bundle
from app.agents.manager.metrics import MIN_SAMPLE, override_rate
from app.agents.manager.orchestrate import assess

GOOD = {"driver": "health", "confidence": 0.95, "repeat_disclosure": False, "rationale": "x",
        "evidence": [{"unit_id": "crm:C-2006#1", "quote": "diagnosed with breast cancer"}]}
FAKE = {"driver": "health", "confidence": 0.9, "repeat_disclosure": False, "rationale": "x",
        "evidence": [{"unit_id": "crm:C-2006#1", "quote": "diagnosed with leukaemia"}]}


def make_call(findings, escalation_down=False):
    calls = []

    async def call(url, text):
        calls.append(url)
        if url == "ingest":
            return json.dumps(fetch_bundle(text), default=str)
        if url == "detection":
            return json.dumps({"member_id": "M-1004", "model": "fake", "tokens": {"in": 1, "out": 1},
                               "result": {"findings": findings, "note": ""}})
        if escalation_down:
            raise ConnectionError("escalation unreachable")
        try:
            return json.dumps(recommend(json.loads(text)))
        except ValueError as exc:
            return json.dumps({"error": str(exc)})
    return call, calls


async def run(findings, escalation_down=False):
    async def pause(seconds):
        pass

    call, calls = make_call(findings, escalation_down)
    case = await assess("M-1004", "ingest", "detection", "escalation", call=call, pause=pause)
    return case, calls


async def main():
    case, calls = await run([GOOD])
    assert case["status"] == "review" and calls.count("escalation") == 1
    assert case["recommendation"]["urgency"] == "high"
    assert case["recommendation"]["headline"].startswith("Possible vulnerability")
    print("verified finding: escalated with a recommendation")

    case, calls = await run([GOOD], escalation_down=True)
    assert case["status"] == "review" and case["recommendation"] is None
    assert len([t for t in case["trail"] if t.startswith("escalation")]) == 2
    print("escalation down: case still reaches the reviewer, failure in the trail")

    case, calls = await run([])
    assert case["status"] == "clean" and "escalation" not in calls
    print("clean case: escalation never called")

    case, calls = await run([FAKE])
    assert case["status"] == "review" and not case["accepted"] and "escalation" not in calls
    print("fabricated finding: rejected, escalation never called (gate 3)")


asyncio.run(main())


def decided(n_confirm, n_dismiss):
    rows = [{"decision": "confirm"}] * n_confirm + [{"decision": "dismiss"}] * n_dismiss
    return [{"decisions": rows}]


assert override_rate([])["rate"] is None
assert override_rate(decided(MIN_SAMPLE - 1, 0))["signal"] == "insufficient_data"
assert override_rate(decided(MIN_SAMPLE, 0))["signal"] == "rubber_stamp_risk"
r = override_rate(decided(MIN_SAMPLE - 1, 1))
assert r["signal"] == "ok" and r["rate"] == 0.1
print("override rate: ok")
print("all wiring tests passed")
