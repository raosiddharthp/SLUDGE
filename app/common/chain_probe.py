"""Ingest -> Detection over A2A, for one member. python -m app.common.chain_probe M-1004"""
import asyncio
import json
import os
import sys

from app.common.a2a_client import call_agent

INGEST_URL = os.environ.get("SLUDGE_INGEST_URL", "http://localhost:8001")
DETECTION_URL = os.environ.get("SLUDGE_DETECTION_URL", "http://localhost:8002")


async def main(member_id):
    bundle_text = await call_agent(INGEST_URL, f"Fetch records for {member_id}")
    print("ingest ->", {k: len(v) for k, v in json.loads(bundle_text).items() if isinstance(v, list)})
    result = json.loads(await call_agent(DETECTION_URL, bundle_text, timeout=60))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
