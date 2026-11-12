"""Deterministic grounding gates. Plain code decides what passes; no LLM is involved."""
from app.common.records import index_records

CONFIDENCE_CEILING = 0.8  # applies when no cited record is the member's own words


def _own_words(rec):
    return rec["text"].startswith("CALLER:")


def review_finding(finding, records):
    """Return (finding, notes). finding is None when it is rejected; notes say why."""
    evidence = finding.get("evidence") or []
    if not evidence:
        return None, ["no evidence cited"]
    for e in evidence:
        rec = records.get(e.get("unit_id"))
        if rec is None:
            return None, [f"cited record {e.get('unit_id')} does not exist"]
        quote = e.get("quote") or ""
        if not quote.strip() or quote not in rec["text"]:
            return None, [f"quote not found verbatim in {e['unit_id']}"]
    own = any(_own_words(records[e["unit_id"]]) for e in evidence)
    out = dict(finding)
    notes = []
    if out["confidence"] > CONFIDENCE_CEILING and not own:
        out["confidence"] = CONFIDENCE_CEILING
        notes.append(f"confidence capped at {CONFIDENCE_CEILING}: no member words cited")
    if out.get("repeat_disclosure") and not own:
        out["repeat_disclosure"] = False
        notes.append("repeat_disclosure cleared: no member words cited")
    return out, notes


def review(bundle, findings):
    """Split findings into accepted (possibly adjusted) and rejected, each with reasons."""
    records = index_records(bundle)
    accepted, rejected = [], []
    for f in findings:
        out, notes = review_finding(f, records)
        if out is None:
            rejected.append({"finding": f, "reasons": notes})
        else:
            accepted.append({"finding": out, "notes": notes})
    return accepted, rejected
