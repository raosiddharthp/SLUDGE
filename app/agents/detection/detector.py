"""Detection logic: one member's records in, cited FG21/1 findings out.

  python -m app.agents.detection.detector M-1004
  python -m app.agents.detection.detector M-1004 --show-prompt
"""
import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.agents.detection.schema import DetectionResult
from app.common.records import index_records

load_dotenv()
MODEL = os.environ.get("SLUDGE_MODEL", "gemini-3.5-flash-lite")
TIMEOUT_S = float(os.environ.get("SLUDGE_DETECT_TIMEOUT_S", "30"))

SYSTEM = """You are the Detection Agent in a Consumer Duty outcomes copilot for a UK building society.
Assess ONE member's recent interactions for signs of vulnerability, using the four FCA FG21/1 drivers:
- health: a condition or illness the records explicitly state, affecting the ability to manage money
- life_events: major events such as bereavement, relationship breakdown or job loss
- resilience: low ability to absorb a financial or emotional shock, e.g. missed payments or signs of distress
- capability: difficulty with money or digital tasks, e.g. repeated failure on a journey or trouble reading

Rules:
1. Use only the records provided. Every finding needs evidence: the record ID exactly as shown in square brackets, and a quote copied word for word from that record. Cite every record that directly supports the finding (up to 4), including the member's own words and any objective records that agree or disagree with them.
2. Assign a driver only when the records state it or directly show it. Do not assign health because a member struggles with a task such as reading small print; health needs an explicitly stated condition. Do not assign a second driver for the same evidence.
3. Never infer vulnerability from age alone. A member saying they are fine does not cancel objective signals: cite the statement and the objective records together.
4. Set repeat_disclosure to true only when the member's own words say they have already told the organisation about this.
5. Confidence is 0 to 1. Use 0.9 or above only when the member states it in their own words. Objective signals alone score 0.8 at most. Use below 0.5 when the evidence is indirect.
6. rationale and note must restate only what the cited records say. Do not add details that are not in them, such as treatment stages, timelines or who spoke to the member.
7. If there is no evidence of any driver, return an empty findings list and say so in note.
8. Keep rationale and note to one or two plain sentences. Do not recommend actions."""


def build_prompt(bundle):
    units = index_records(bundle)
    rows = sorted(units.items(), key=lambda kv: kv[1]["date"])
    lines = [f"[{uid}] ({u['system']}, {u['date']}) {u['text']}" for uid, u in rows]
    age = (bundle.get("member") or {}).get("age", "unknown")
    return f"Member age: {age}\nRecords:\n" + "\n".join(lines)


def detect(bundle):
    out = {"member_id": bundle["member_id"], "model": MODEL}
    try:
        client = genai.Client(http_options=types.HttpOptions(timeout=int(TIMEOUT_S * 1000)))
        resp = client.models.generate_content(
            model=MODEL,
            contents=build_prompt(bundle),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                response_mime_type="application/json",
                response_schema=DetectionResult,
                temperature=0,
                seed=7,
            ),
        )
    except Exception as exc:  # timeouts, rate limits, network: the Manager treats any error as a failed check
        out["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
        return out
    usage = resp.usage_metadata
    out["tokens"] = {"in": usage.prompt_token_count, "out": usage.candidates_token_count}
    if resp.parsed is None:
        out["error"] = "model output did not match the schema"
        out["raw"] = resp.text
    else:
        out["result"] = resp.parsed.model_dump(mode="json")
    return out


if __name__ == "__main__":
    from app.agents.ingest.sources import fetch_bundle

    bundle = fetch_bundle(sys.argv[1])
    if "--show-prompt" in sys.argv:
        print(build_prompt(bundle))
    else:
        print(json.dumps(detect(bundle), indent=2))
