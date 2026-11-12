"""Flatten Firestore case documents into rows for the governed BigQuery dataset."""
import json


def _ts(value):
    return value.isoformat() if value is not None else None


def case_row(c):
    rec = c.get("recommendation") or {}
    tokens = c.get("tokens") or {}
    return {
        "case_id": c["case_id"], "member_id": c["member_id"], "status": c["status"],
        "review_state": c.get("review_state"), "outcome": c.get("outcome"), "stage": c.get("stage"),
        "model": c.get("model"), "tokens_in": tokens.get("in"), "tokens_out": tokens.get("out"),
        "accepted_n": len(c.get("accepted") or []), "rejected_n": len(c.get("rejected") or []),
        "failed_attempts": len(c.get("trail") or []),
        "urgency": rec.get("urgency"), "headline": rec.get("headline"),
        "created_at": _ts(c.get("created_at")), "decided_at": _ts(c.get("decided_at")),
        "reviewer": c.get("reviewer"), "lawful_basis": c.get("lawful_basis"),
        "retain_until": _ts(c.get("retain_until")), "review_note": c.get("review_note"),
    }


def _finding(base, i, f, grounded, adjusted, decision):
    return {**base, "idx": i, "driver": f.get("driver"), "confidence": f.get("confidence"),
            "repeat_disclosure": bool(f.get("repeat_disclosure")), "grounded": grounded,
            "adjusted": adjusted, "decision": decision, "evidence_n": len(f.get("evidence") or []),
            "rationale": f.get("rationale"), "evidence": json.dumps(f.get("evidence") or [])}


def finding_rows(c):
    """One row per finding the model produced: accepted ones carry the decision, rejected ones do not."""
    decisions = {d["index"]: d["decision"] for d in c.get("decisions") or []}
    base = {"case_id": c["case_id"], "member_id": c["member_id"], "created_at": _ts(c.get("created_at"))}
    rows = [_finding(base, i, a["finding"], True, bool(a.get("notes")), decisions.get(i))
            for i, a in enumerate(c.get("accepted") or [])]
    rows += [_finding(base, i, r["finding"], False, False, None)
             for i, r in enumerate(c.get("rejected") or [])]
    return rows
