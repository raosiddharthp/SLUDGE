import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
MODEL = os.environ.get("SLUDGE_MODEL", "gemini-2.5-flash-lite")


class Ping(BaseModel):
    ok: bool
    note: str


client = genai.Client()

print("Flash-Lite models visible to this key:")
for m in client.models.list():
    if "flash-lite" in m.name:
        print(" ", m.name)

resp = client.models.generate_content(
    model=MODEL,
    contents="Return ok=true and a five-word note.",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Ping,
    ),
)
print(resp.parsed)
print("tokens in/out:",
      resp.usage_metadata.prompt_token_count,
      resp.usage_metadata.candidates_token_count)
print("thinking tokens:", getattr(resp.usage_metadata, "thoughts_token_count", None))
