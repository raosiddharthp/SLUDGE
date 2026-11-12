"""Citable records. Shared by Detection (to cite) and Manager (to verify citations).

Turns an Ingest bundle into units: {unit_id: {"system", "date", "text"}}.
IDs are built from natural keys, with timestamps normalised to UTC, so the same
bundle always produces the same IDs whichever source it was read from.
"""
from datetime import datetime, timezone


def _utc(ts):
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def index_records(bundle):
    units = {}
    for e in bundle.get("app_events", []):
        ts = _utc(e["ts"])
        units[f"app:{ts}"] = {
            "system": "member_app", "date": ts[:10],
            "text": f"{e['event']} at step '{e['step']}' -> {e['outcome']}",
        }
    for c in bundle.get("crm_notes", []):
        ts = _utc(c["ts"])
        cid = c["call_id"]
        units[f"crm:{cid}#note"] = {"system": "contact_centre_crm", "date": ts[:10], "text": c["agent_note"]}
        for i, line in enumerate(c.get("transcript_excerpt", []), start=1):
            units[f"crm:{cid}#{i}"] = {"system": "contact_centre_crm", "date": ts[:10], "text": line}
    for t in bundle.get("core_txns", []):
        ts = _utc(t["ts"])
        units[f"core:{ts}:{t['type']}"] = {
            "system": "core_banking", "date": ts[:10],
            "text": f"{t['type']} GBP {t['amount_gbp']:.2f} {t['status']}",
        }
    return units
