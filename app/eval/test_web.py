from datetime import date, datetime, timezone

from starlette.testclient import TestClient

from app.web.cache import TTLCache
from app.web.server import make_app

CID = "M-1004-20261113T085225Z-e7516f"


class Fake:
    def __init__(self):
        self.calls = {"lens": 0, "case": 0}
        self.lens_fail = False

    def queue(self):
        return [{"case_id": CID, "created_at": datetime(2026, 11, 13, 8, 52, tzinfo=timezone.utc)}]

    def override(self):
        return {"decided_findings": 1, "overridden": 0, "rate": 0.0, "signal": "insufficient_data"}

    def case(self, case_id):
        self.calls["case"] += 1
        return {"case_id": case_id, "status": "review"} if case_id == CID else None

    def lens(self, name):
        self.calls["lens"] += 1
        if self.lens_fail:
            raise RuntimeError("bq down")
        return [{"day": date(2026, 11, 13), "n": 1}]


def build():
    t = [0.0]
    fake = Fake()
    return fake, t, TestClient(make_app(fake, TTLCache(300, clock=lambda: t[0])))


fake, t, client = build()
assert client.get("/healthz").json() == {"ok": True}
assert client.get("/api/queue").json()["queue"][0]["created_at"] == "2026-11-13T08:52:00+00:00"
assert client.get("/api/override").json()["signal"] == "insufficient_data"

for bad in ["x", "M-1004", "M-1004-20261113T085225Z-E7516F", "..%2F..%2Fx", "a%2Fb"]:
    assert client.get(f"/api/case/{bad}").status_code == 404, bad
assert fake.calls["case"] == 0
assert client.get("/api/case/M-1004-20261113T085225Z-000000").status_code == 404
assert client.get(f"/api/case/{CID}").json()["status"] == "review"

assert client.get("/api/lens/nope").status_code == 404 and fake.calls["lens"] == 0
r = client.get("/api/lens/ledger")
assert r.status_code == 200 and r.json()["rows"][0]["day"] == "2026-11-13"
client.get("/api/lens/ledger")
assert fake.calls["lens"] == 1
client.get("/api/lens/redact")
assert fake.calls["lens"] == 2
t[0] = 301
client.get("/api/lens/ledger")
assert fake.calls["lens"] == 3

fake.lens_fail = True
r = client.get("/api/lens/trustwell")
assert r.status_code == 502 and "bq down" not in r.text
fake.lens_fail = False
assert client.get("/api/lens/trustwell").status_code == 200
print("all web tests passed")
