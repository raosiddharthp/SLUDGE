"""python -m app.eval.replay <case_id>: re-check a stored case offline. No LLM, no cost."""
import sys

from google.cloud.firestore_v1.base_query import FieldFilter

from app.agents.ingest.sources import fetch_bundle
from app.agents.manager.replay import replay, reproduced
from app.agents.manager.store import COLLECTION, _db


def main(case_id):
    query = _db().collection(COLLECTION).where(filter=FieldFilter("case_id", "==", case_id)).limit(1)
    snap = next(iter(query.stream()), None)
    if snap is None:
        sys.exit(f"no such case: {case_id}")
    case = snap.to_dict()
    result = replay(case, fetch_bundle(case["member_id"]))
    print(result)
    ok = reproduced(result)
    print("REPRODUCED" if ok else "MISMATCH")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1])
