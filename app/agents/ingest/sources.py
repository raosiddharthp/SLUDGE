"""Read-only data access for the Ingest Agent. This module only ever reads."""
import os
from datetime import datetime

PROJECT = os.environ.get("SLUDGE_GCP_PROJECT", "lumen-poc-srao26")
PREFIX = os.environ.get("SLUDGE_FS_PREFIX", "sludge_")
SOURCE = os.environ.get("SLUDGE_SOURCE", "firestore")  # "firestore" or "seed" (offline)

SOURCE_SYSTEMS = {
    "app_events": "member_app",
    "crm_notes": "contact_centre_crm",
    "core_txns": "core_banking",
}


def _clean(doc):
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in doc.items()}


def _reader():
    if SOURCE == "seed":
        from app.data.seed_data import SEED
        return lambda kind, mid: [dict(r) for r in SEED[kind] if r["member_id"] == mid]
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    db = firestore.Client(project=PROJECT)

    def read(kind, mid):
        q = db.collection(PREFIX + kind).where(filter=FieldFilter("member_id", "==", mid))
        return [_clean(d.to_dict()) for d in q.stream()]
    return read


def fetch_bundle(member_id):
    read = _reader()
    members = read("members", member_id)
    bundle = {
        "member_id": member_id,
        "found": bool(members),
        "member": members[0] if members else None,
        "source": SOURCE,
        "source_systems": SOURCE_SYSTEMS,
    }
    for kind in SOURCE_SYSTEMS:
        bundle[kind] = sorted(read(kind, member_id), key=lambda r: r["ts"])
    return bundle
