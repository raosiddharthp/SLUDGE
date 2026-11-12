"""Seed the SLUDGE synthetic data into Firestore.

Safe to re-run: document IDs are deterministic, so a re-run overwrites
the same documents instead of duplicating them.

Run from the repo root:
  python -m app.data.seed_firestore            dry run, writes nothing
  python -m app.data.seed_firestore --write    write to Firestore
  python -m app.data.seed_firestore --check    count docs per collection
"""
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from app.data.seed_data import SEED

load_dotenv()
PROJECT = os.environ.get("SLUDGE_GCP_PROJECT", "lumen-poc-srao26")
PREFIX = os.environ.get("SLUDGE_FS_PREFIX", "sludge_")
# Bill API quota to this project only, without touching the machine-wide ADC file.
os.environ.setdefault("GOOGLE_CLOUD_QUOTA_PROJECT", PROJECT)


def doc_id(kind, row):
    if kind == "members":
        return row["member_id"]
    if kind == "crm_notes":
        return row["call_id"]
    return f'{row["member_id"]}_{row["ts"]}'.replace(":", "")


def to_doc(row):
    doc = dict(row)
    if "ts" in doc:
        doc["ts"] = datetime.fromisoformat(doc["ts"].replace("Z", "+00:00"))
    return doc


def main(mode):
    db = None
    if mode in ("write", "check"):
        from google.cloud import firestore  # imported late so a dry run needs no cloud setup
        db = firestore.Client(project=PROJECT)
    print(f"project={PROJECT} prefix={PREFIX} mode={mode}")

    total = 0
    for kind, rows in SEED.items():
        coll = f"{PREFIX}{kind}"
        ids = [doc_id(kind, r) for r in rows]
        assert len(ids) == len(set(ids)), f"duplicate document IDs in {kind}"
        docs = [to_doc(r) for r in rows]  # validate conversion even on a dry run
        if mode == "write":
            for doc, did in zip(docs, ids):
                db.collection(coll).document(did).set(doc)
        if mode == "check":
            n = int(db.collection(coll).count().get()[0][0].value)
            print(f"{coll}: {n} docs in Firestore (expected {len(rows)})")
        else:
            print(f"{coll}: {len(rows)} docs")
        total += len(rows)
    print({"write": "written", "check": "checked", "dry": "dry run, nothing written"}[mode], total)


if __name__ == "__main__":
    flag = sys.argv[1] if len(sys.argv) > 1 else ""
    main({"--write": "write", "--check": "check", "": "dry"}[flag])
