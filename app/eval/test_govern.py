import asyncio

from app.agents.manager.govern import notify_governance


def run(url, call, timeout=25):
    return asyncio.run(notify_governance(url, call, timeout))


async def ok(url, text):
    return '{"cases": 7, "findings": 8}'


async def reports_error(url, text):
    return '{"error": "sync failed: Forbidden"}'


async def raises(url, text):
    raise ConnectionError("down")


async def hangs(url, text):
    await asyncio.sleep(5)


assert run("http://g", ok) == "synced"
assert run("", ok).startswith("skipped")
assert run("http://g", reports_error).startswith("failed")
assert run("http://g", raises) == "skipped: ConnectionError"
assert run("http://g", hangs, timeout=0.1) == "skipped: TimeoutError"
print("all govern tests passed")
