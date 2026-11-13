"""Real data layer: Firestore for cases, BigQuery for the lens views."""
import os

from google.cloud import bigquery

from app.agents.manager.queue import override_stats, pending_queue
from app.agents.manager.store import COLLECTION, _db
from app.web.rules import LENSES

PROJECT = os.environ.get("SLUDGE_PROJECT", "lumen-poc-srao26")
DATASET = "sludge_gov"
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
