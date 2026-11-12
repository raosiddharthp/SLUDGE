"""Sync Firestore cases into the governed BigQuery dataset. Full snapshot, so it is idempotent."""
import os

from google.cloud import bigquery

from app.agents.governance.flatten import case_row, finding_rows
from app.agents.manager.store import COLLECTION, _db

PROJECT = os.environ.get("SLUDGE_PROJECT", "lumen-poc-srao26")
DATASET = "sludge_gov"

CASES = [
    ("case_id", "STRING"), ("member_id", "STRING"), ("status", "STRING"), ("review_state", "STRING"),
    ("outcome", "STRING"), ("stage", "STRING"), ("model", "STRING"), ("tokens_in", "INT64"),
    ("tokens_out", "INT64"), ("accepted_n", "INT64"), ("rejected_n", "INT64"),
    ("failed_attempts", "INT64"), ("urgency", "STRING"), ("headline", "STRING"),
    ("created_at", "TIMESTAMP"), ("decided_at", "TIMESTAMP"), ("reviewer", "STRING"),
    ("lawful_basis", "STRING"), ("retain_until", "TIMESTAMP"),
    ("review_note", "STRING"),
]
FINDINGS = [
    ("case_id", "STRING"), ("member_id", "STRING"), ("created_at", "TIMESTAMP"), ("idx", "INT64"),
    ("driver", "STRING"), ("confidence", "FLOAT64"), ("repeat_disclosure", "BOOL"),
    ("grounded", "BOOL"), ("adjusted", "BOOL"), ("decision", "STRING"), ("evidence_n", "INT64"),
    ("rationale", "STRING"), ("evidence", "STRING"),
]


def _load(bq, table, schema, rows):
    ref = f"{PROJECT}.{DATASET}.{table}"
    fields = [bigquery.SchemaField(name, kind) for name, kind in schema]
    bq.create_table(bigquery.Table(ref, schema=fields), exists_ok=True)
    if not rows:
        bq.query(f"TRUNCATE TABLE `{ref}`").result()
        return
    config = bigquery.LoadJobConfig(schema=fields, write_disposition="WRITE_TRUNCATE")
    bq.load_table_from_json(rows, ref, job_config=config).result()


def sync():
    """Replace both governed tables with the current contents of Firestore."""
    cases = [d.to_dict() for d in _db().collection(COLLECTION).stream()]
    bq = bigquery.Client(project=PROJECT)
    case_rows = [case_row(c) for c in cases]
    f_rows = [r for c in cases for r in finding_rows(c)]
    _load(bq, "cases", CASES, case_rows)
    _load(bq, "findings", FINDINGS, f_rows)
    return {"cases": len(case_rows), "findings": len(f_rows)}


if __name__ == "__main__":
    print(sync())
