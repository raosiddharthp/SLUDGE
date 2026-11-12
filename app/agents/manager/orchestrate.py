"""Manager orchestration: Ingest -> Detection -> gates -> Escalation, each stage retried once."""
import asyncio
import json

from app.agents.manager.gates import review
from app.common.a2a_client import call_agent


async def _stage(call, stage, url, text, pause, backoff, trail):
    """Call one agent; retry once after a pause. Returns (raw_text, parsed) or (None, None)."""
    for attempt in (1, 2):
        try:
            raw = await call(url, text)
            out = json.loads(raw)
            if not (isinstance(out, dict) and "error" in out):
                return raw, out
            trail.append(f"{stage} attempt {attempt}: {str(out['error'])[:120]}")
        except Exception as exc:
            trail.append(f"{stage} attempt {attempt}: {type(exc).__name__}: {str(exc)[:120]}")
        if attempt == 1:
            await pause(backoff)
    return None, None


async def assess(member_id, ingest_url, detection_url, escalation_url=None,
                 call=call_agent, pause=asyncio.sleep, backoff=4.0):
    """Run one member through the pipeline and return a case record."""
    trail = []
    case = {"member_id": member_id, "trail": trail}

    ingest_raw, bundle = await _stage(call, "ingest", ingest_url, member_id, pause, backoff, trail)
    if bundle is None:
        return {**case, "status": "queued_error", "stage": "ingest"}

    _, detection = await _stage(call, "detection", detection_url, ingest_raw, pause, backoff, trail)
    if detection is None:
        return {**case, "status": "queued_error", "stage": "detection"}

    result = detection.get("result") or {}
    accepted, rejected = review(bundle, result.get("findings") or [])
    status = "review" if (accepted or rejected) else "clean"
    out = {
        **case,
        "status": status,
        "model": detection.get("model"),
        "tokens": detection.get("tokens"),
        "accepted": accepted,
        "rejected": rejected,
        "note": result.get("note"),
        "recommendation": None,
    }
    # Gate 3: only verified, grounded findings ever reach Escalation.
    if accepted and escalation_url:
        verified = {"member_id": member_id, "status": status, "accepted": accepted}
        _, rec = await _stage(call, "escalation", escalation_url, json.dumps(verified), pause, backoff, trail)
        out["recommendation"] = rec
    return out
