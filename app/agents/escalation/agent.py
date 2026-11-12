"""Escalation Agent exposed over A2A. Input: a verified Manager case as JSON text. Output: a recommendation."""
import json
import os
from typing import AsyncGenerator

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from app.agents.escalation.recommend import recommend


class EscalationAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        parts = ctx.user_content.parts if ctx.user_content else []
        text = " ".join(p.text for p in parts if p.text)
        try:
            payload = recommend(json.loads(text))
        except (ValueError, TypeError, AttributeError) as exc:
            payload = {"error": f"cannot escalate: {exc}"}
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload))]),
        )


root_agent = EscalationAgent(
    name="escalation",
    description="Given a verified case with at least one grounded finding, returns a plain-language "
                "recommendation for the human reviewer. Rule-based; refuses unverified input.",
)

a2a_app = to_a2a(
    root_agent,
    host=os.environ.get("A2A_HOST", "localhost"),
    port=int(os.environ.get("A2A_PORT", "8004")),
    protocol=os.environ.get("A2A_PROTOCOL", "http"),
)
