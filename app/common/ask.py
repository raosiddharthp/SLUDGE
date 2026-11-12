"""Send one message to an A2A agent and pretty-print its JSON result (120 s timeout)."""
import asyncio
import json
import sys

from app.common.a2a_client import call_agent

text = asyncio.run(call_agent(sys.argv[1], sys.argv[2], timeout=120))
try:
    print(json.dumps(json.loads(text), indent=2))
except ValueError:
    print(text)
