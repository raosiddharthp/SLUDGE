"""Tiny A2A client for poking an agent.

  python -m app.common.a2a_probe URL "message"
"""
import asyncio
import json
import sys
import uuid

from a2a.client import create_client
from a2a.types import Message, Part, Role, SendMessageRequest, TaskState


def show_artifact(artifact):
    text = "".join(p.text for p in artifact.parts if p.text)
    try:
        data = json.loads(text)
    except ValueError:
        print("  artifact (text):", text[:500])
        return
    if isinstance(data, dict) and "member_id" in data:
        counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
        print("  artifact: member", data["member_id"], "found:", data.get("found"), "records:", counts)
    else:
        print("  artifact:", json.dumps(data)[:500])


async def main(url, text):
    client = await create_client(url)
    request = SendMessageRequest(
        message=Message(message_id=str(uuid.uuid4()), role=Role.ROLE_USER, parts=[Part(text=text)])
    )
    async for response in client.send_message(request):
        field, value = response.ListFields()[0]
        if field.name == "status_update":
            print("state:", TaskState.Name(value.status.state))
        elif field.name == "artifact_update":
            show_artifact(value.artifact)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
