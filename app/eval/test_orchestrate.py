"""Offline test of the Manager's orchestration: happy path, retry, outage, fabrication, clean."""
import asyncio
import json

from app.agents.ingest.sources import fetch_bundle
from app.agents.manager.orchestrate import assess

GOOD = {"driver": "health", "confidence": 0.95, "repeat_disclosure": False, "rationale": "x",
        "evidence": [{"unit_id": "crm:C-2006#1", "quote": "diagnosed with breast cancer"}]}
FAKE = {"driver": "health", "confidence": 0.9, "repeat_disclosure": False, "rationale": "x",
        "evidence": [{"unit_id": "crm:C-2006#1", "quote": "diagnosed with leukaemia"}]}


def make_call(findings, fail_first=0):
    state = {"detection_calls": 0}

    async def call(url, text):
        if url == "ingest":
            return json.dumps(fetch_bundle(text), default=str)
        state["detection_calls"] += 1
        if state["detection_calls"] <= fail_first:
            return json.dumps({"error": "ServerError: 503 UNAVAILABLE"})
        return json.dumps({"member_id": "M-1004", "model": "fake", "tokens": {"in": 1, "out": 1},
                           "result": {"findings": findings, "note": ""}})
    return call, state


async def run(findings, fail_first=0):
    pauses = []

    async def pause(seconds):
        pauses.append(seconds)

    call, _ = make_call(findings, fail_first)
    case = await assess("M-1004", "ingest", "detection", call=call, pause=pause)
    return case, pauses


async def main():
    case, pauses = await run([GOOD])
    assert case["status"] == "review" and len(case["accepted"]) == 1 and not case["trail"] and not pauses
    print("happy path: ok")

    case, pauses = await run([GOOD], fail_first=1)
    assert case["status"] == "review" and len(case["trail"]) == 1 and len(pauses) == 1
    print("one 503 then success: ok, retried once")

    case, pauses = await run([GOOD], fail_first=5)
    assert case["status"] == "queued_error" and case["stage"] == "detection" and len(case["trail"]) == 2
    print("outage: ok, queued for a human with", len(case["trail"]), "trail entries")

    case, _ = await run([FAKE])
    assert case["status"] == "review" and not case["accepted"] and len(case["rejected"]) == 1
    print("fabricated quote: ok, rejected and flagged")

    case, _ = await run([])
    assert case["status"] == "clean"
    print("no findings: ok, clean")
    print("all orchestration tests passed")


asyncio.run(main())
