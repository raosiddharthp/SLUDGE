"""Detection Agent exposed over A2A. Input: an Ingest bundle as JSON text. Output: findings JSON."""
import asyncio
import json
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from app.agents.detection.detector import detect

load_dotenv()


class DetectionAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        parts = ctx.user_content.parts if ctx.user_content else []
        text = " ".join(p.text for p in parts if p.text)
        try:
            bundle = json.loads(text)
            if not isinstance(bundle, dict) or "member_id" not in bundle:
                raise ValueError("no member_id")
        except ValueError:
            payload = {"error": "expected an Ingest bundle as JSON text, including a member_id"}
        else:
            payload = await asyncio.to_thread(detect, bundle)  # keep the event loop free during the model call
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload))]),
        )


root_agent = DetectionAgent(
    name="detection",
    description="Given a member's Ingest bundle as JSON, assesses it against the four FCA FG21/1 "
                "vulnerability drivers using Gemini. Every finding cites record IDs and verbatim quotes.",
)

a2a_app = to_a2a(
    root_agent,
    host=os.environ.get("A2A_HOST", "localhost"),
    port=int(os.environ.get("A2A_PORT", "8002")),
    protocol=os.environ.get("A2A_PROTOCOL", "http"),
)
