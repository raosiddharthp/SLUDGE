"""Persist case records to Firestore (collection sludge_cases). The Manager is the only agent that writes."""
import os
import uuid
from datetime import datetime, timedelta, timezone

from google.cloud import firestore

os.environ.setdefault("GOOGLE_CLOUD_QUOTA_PROJECT", "lumen-poc-srao26")
COLLECTION = "sludge_cases"
LAWFUL_BASIS = "consumer_duty_monitoring"  # POC placeholder; a DPO decides in production
RETENTION_DAYS = int(os.environ.get("SLUDGE_RETENTION_DAYS", "90"))
_client = None


def _db():
    global _client
    if _client is None:
        _client = firestore.Client()
    return _client


def save_case(case):
    """Write one case and return its ID. Clean cases are closed; all others wait for a human."""
    now = datetime.now(timezone.utc)
    case_id = f"{case['member_id']}-{now:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"
    doc = dict(case)
    doc["case_id"] = case_id
    doc["review_state"] = "closed_clean" if case["status"] == "clean" else "pending"
    doc["created_at"] = now
    doc["lawful_basis"] = LAWFUL_BASIS
    doc["retain_until"] = now + timedelta(days=RETENTION_DAYS)
    _db().collection(COLLECTION).document(case_id).set(doc)
    return case_id
