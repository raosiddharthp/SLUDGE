"""Manager Agent exposed over A2A. Input: a member ID. Output: the case record as JSON."""
import asyncio
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

from app.agents.manager.govern import notify_governance
from app.agents.manager.orchestrate import assess
from app.agents.manager.store import save_case
from app.common.a2a_client import call_agent

load_dotenv()

INGEST_URL = os.environ.get("SLUDGE_INGEST_URL", "http://localhost:8001")
DETECTION_URL = os.environ.get("SLUDGE_DETECTION_URL", "http://localhost:8002")
ESCALATION_URL = os.environ.get("SLUDGE_ESCALATION_URL", "http://localhost:8004")
GOVERNANCE_URL = os.environ.get("SLUDGE_GOVERNANCE_URL", "")


class ManagerAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        parts = ctx.user_content.parts if ctx.user_content else []
        text = " ".join(p.text for p in parts if p.text)
        match = re.search(r"M-\d{4}", text)
        if match:
            payload = await assess(match.group(0), INGEST_URL, DETECTION_URL, ESCALATION_URL)
            if os.environ.get("SLUDGE_STORE") == "firestore":
                try:
                    payload["case_id"] = await asyncio.to_thread(save_case, payload)
                except Exception as exc:
                    payload["store_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
                else:
                    payload["governance"] = await notify_governance(GOVERNANCE_URL, call_agent)
        else:
            payload = {"error": "expected a member ID such as M-1001"}
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload, default=str))]),
        )


root_agent = ManagerAgent(
    name="manager",
    description="Orchestrates one member's assessment: calls Ingest, then Detection, retries a failed "
                "stage once, verifies every cited quote against the source records, and returns the case.",
)

a2a_app = to_a2a(
    root_agent,
    host=os.environ.get("A2A_HOST", "localhost"),
    port=int(os.environ.get("A2A_PORT", "8003")),
    protocol=os.environ.get("A2A_PROTOCOL", "http"),
)
