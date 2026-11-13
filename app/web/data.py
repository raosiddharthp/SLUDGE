"""Real data layer: Firestore for cases, BigQuery for the lens views, the Manager for assessments."""
import asyncio
import json
import os

from google.cloud import bigquery

from app.agents.manager.decisions import decide_case
from app.agents.manager.govern import notify_governance
from app.agents.manager.queue import override_stats, pending_queue
from app.agents.manager.store import COLLECTION, RETENTION_DAYS, _db
from app.common import cap
from app.common.a2a_client import call_agent
from app.web import audit
from app.web.rules import LENSES

PROJECT = os.environ.get("SLUDGE_PROJECT", "lumen-poc-srao26")
DATASET = "sludge_gov"
MANAGER_URL = os.environ.get("SLUDGE_MANAGER_URL", "")
GOVERNANCE_URL = os.environ.get("SLUDGE_GOVERNANCE_URL", "")
SYNC_WAIT = 10  # seconds the reviewer waits for the governed dataset to catch up
MAX_BYTES_BILLED = 100 * 1024 * 1024  # hard ceiling per lens query


def queue():
    return pending_queue()


def override():
    return override_stats()


def case(case_id):
    snap = _db().collection(COLLECTION).document(case_id).get()
    return snap.to_dict() if snap.exists else None


def lens(name):
    assert name in LENSES, name
    sql = f"SELECT * FROM `{PROJECT}.{DATASET}.lens_{name}` ORDER BY 1 DESC LIMIT 50"
    config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_BILLED)
    rows = bigquery.Client(project=PROJECT).query(sql, job_config=config).result()
    return [dict(r.items()) for r in rows]


def usage():
    return cap.peek(_db())


def take_slot():
    return cap.take(_db())


def assess(member_id):
    """Call the private Manager. The slot has already been taken by the caller."""
    if not MANAGER_URL:
        raise RuntimeError("SLUDGE_MANAGER_URL is not configured")
    out = json.loads(asyncio.run(call_agent(MANAGER_URL, member_id, timeout=170)))
    return {k: out.get(k) for k in ("case_id", "status", "governance", "store_error")}


def decide(case_id, decisions, reviewer, note):
    update = decide_case(case_id, decisions, reviewer, note)
    sync = asyncio.run(notify_governance(GOVERNANCE_URL, call_agent, timeout=SYNC_WAIT))
    return {"outcome": update["outcome"], "review_state": update["review_state"], "governance": sync}


def log_view(case_id, member_id):
    audit.record(_db(), case_id, member_id, RETENTION_DAYS)
