"""Call an A2A agent and return the text of its result artifact. Reused by the Manager."""
import asyncio
import os
import uuid

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest


def _id_token(url):
    """Cloud Run agents require a Google ID token. Locally, export SLUDGE_ID_TOKEN; on Cloud Run it is fetched."""
    token = os.environ.get("SLUDGE_ID_TOKEN")
    if token or not url.startswith("https://"):
        return token
    import google.auth.transport.requests
    import google.oauth2.id_token
    return google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), url)


async def call_agent(url, text, timeout=60):
    token = await asyncio.to_thread(_id_token, url)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    # create_client() defaults to httpx's 5-second timeout, which a slow model call exceeds.
    http = httpx.AsyncClient(timeout=httpx.Timeout(timeout), headers=headers)
    client = await create_client(url, client_config=ClientConfig(httpx_client=http))
    result = None

    async def run():
        nonlocal result
        request = SendMessageRequest(
            message=Message(message_id=str(uuid.uuid4()), role=Role.ROLE_USER, parts=[Part(text=text)])
        )
        async for response in client.send_message(request):
            field, value = response.ListFields()[0]
            if field.name == "artifact_update":
                result = "".join(p.text for p in value.artifact.parts if p.text)

    try:
        await asyncio.wait_for(run(), timeout)
    finally:
        await client.close()
        await http.aclose()
    if result is None:
        raise RuntimeError(f"{url} returned no artifact")
    return result
