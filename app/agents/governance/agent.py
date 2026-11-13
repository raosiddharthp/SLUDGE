"""Governance Agent exposed over A2A. Any input triggers a Firestore to BigQuery snapshot sync."""
import os
from typing import AsyncGenerator
import json

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from app.agents.governance.runner import Coalescer
from app.agents.governance.sync import sync

_sync = Coalescer(sync)


class GovernanceAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            payload = await _sync.run()
        except Exception as exc:
            payload = {"error": f"sync failed: {type(exc).__name__}: {str(exc)[:120]}"}
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload))]),
        )


root_agent = GovernanceAgent(
    name="governance",
    description="Refreshes the governed BigQuery dataset from the case store and returns row counts. "
                "Deterministic; never changes a case.",
)

a2a_app = to_a2a(
    root_agent,
    host=os.environ.get("A2A_HOST", "localhost"),
    port=int(os.environ.get("A2A_PORT", "8005")),
    protocol=os.environ.get("A2A_PROTOCOL", "http"),
)
