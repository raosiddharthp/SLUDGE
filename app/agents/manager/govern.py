"""Ask Governance to refresh the governed dataset. Bounded wait; never raises, never touches the case."""
import asyncio


async def notify_governance(url, call, timeout=25):
    if not url:
        return "skipped: no governance url"
    try:
        raw = await asyncio.wait_for(call(url, "sync"), timeout)
    except Exception as exc:
        return f"skipped: {type(exc).__name__}"
    return "failed: governance reported an error" if '"error"' in str(raw) else "synced"
