"""Ingest Agent: deterministic, read-only, exposed over A2A. No LLM, so no token cost."""
import json
import os
import re
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from app.agents.ingest.sources import fetch_bundle

load_dotenv()
MEMBER_RE = re.compile(r"M-\d{4}")


class IngestAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        parts = ctx.user_content.parts if ctx.user_content else []
        text = " ".join(p.text for p in parts if p.text)
        match = MEMBER_RE.search(text)
        if match:
            payload = fetch_bundle(match.group(0))
        else:
            payload = {"error": "no member_id found; send a message containing e.g. M-1001"}
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload))]),
        )


root_agent = IngestAgent(
    name="ingest",
    description="Read-only. Given a member ID (e.g. M-1001), returns that member's records "
                "from the Member App, Contact Centre CRM and Core Banking as one JSON bundle.",
)

# Public URL details go in the agent card; override these on Cloud Run.
a2a_app = to_a2a(
    root_agent,
    host=os.environ.get("A2A_HOST", "localhost"),
    port=int(os.environ.get("A2A_PORT", "8001")),
    protocol=os.environ.get("A2A_PROTOCOL", "http"),
)
