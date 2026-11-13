import asyncio
import time

from app.agents.governance.runner import Coalescer


def test_overlapping_requests_coalesce():
    calls = []

    def fn():
        calls.append(1)
        time.sleep(0.2)
        return {"n": len(calls)}

    async def go():
        c = Coalescer(fn)
        return await asyncio.gather(*[c.run() for _ in range(5)])

    results = asyncio.run(go())
    assert len(calls) == 2, calls
    assert all(isinstance(r, dict) for r in results)


def test_failure_is_raised_and_next_request_retries():
    state = {"n": 0}

    def fn():
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("bq down")
        return {"ok": True}

    async def go():
        c = Coalescer(fn)
        try:
            await c.run()
            raised = False
        except RuntimeError:
            raised = True
        return raised, await c.run()

    raised, second = asyncio.run(go())
    assert raised and second == {"ok": True}


test_overlapping_requests_coalesce()
test_failure_is_raised_and_next_request_retries()
print("all governance tests passed")
