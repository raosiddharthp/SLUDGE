from datetime import date, datetime, timezone

from starlette.testclient import TestClient

from app.web.cache import TTLCache
from app.web.server import make_app

CID = "M-1004-20261113T085225Z-e7516f"


class Fake:
    def __init__(self):
        self.calls = {"lens": 0, "case": 0, "assess": 0, "slot": 0}
        self.lens_fail = False
        self.log_fail = False
        self.assess_fail = False
        self.slots = 5
        self.decide_error = None
        self.logged, self.decided = [], []

    def queue(self):
        return [{"case_id": CID, "created_at": datetime(2026, 11, 13, 8, 52, tzinfo=timezone.utc)}]

    def override(self):
        return {"decided_findings": 1, "overridden": 0, "rate": 0.0, "signal": "insufficient_data"}

    def usage(self):
        return {"used": 3, "cap": 20, "remaining": 17}

    def case(self, case_id):
        self.calls["case"] += 1
        return {"case_id": case_id, "status": "review", "member_id": "M-1004"} if case_id == CID else None

    def log_view(self, case_id, member_id):
        if self.log_fail:
            raise RuntimeError("firestore down")
        self.logged.append((case_id, member_id))

    def lens(self, name):
        self.calls["lens"] += 1
        if self.lens_fail:
            raise RuntimeError("bq down")
        return [{"day": date(2026, 11, 13), "n": 1}]

    def take_slot(self):
        self.calls["slot"] += 1
        if self.slots <= 0:
            return {"allowed": False, "used": 20, "cap": 20, "remaining": 0}
        self.slots -= 1
        return {"allowed": True, "used": 21 - self.slots, "cap": 20, "remaining": self.slots}

    def assess(self, member_id):
        self.calls["assess"] += 1
        if self.assess_fail:
            raise RuntimeError("manager down")
        return {"case_id": "c1", "status": "clean", "governance": "synced", "store_error": None}

    def decide(self, case_id, decisions, reviewer, note):
        self.decided.append((case_id, decisions, reviewer, note))
        if self.decide_error:
            raise self.decide_error
        return {"outcome": "confirmed", "review_state": "decided"}


def build():
    t = [0.0]
    fake = Fake()
    return fake, t, TestClient(make_app(fake, TTLCache(300, clock=lambda: t[0])))


# --- read side
fake, t, client = build()
assert client.get("/health").json() == {"ok": True}
assert client.get("/api/queue").json()["queue"][0]["created_at"] == "2026-11-13T08:52:00+00:00"
assert client.get("/api/override").json()["signal"] == "insufficient_data"
assert client.get("/api/usage").json() == {"used": 3, "cap": 20, "remaining": 17}

for bad in ["x", "M-1004", "M-1004-20261113T085225Z-E7516F", "..%2F..%2Fx", "a%2Fb"]:
    assert client.get(f"/api/case/{bad}").status_code == 404, bad
assert fake.calls["case"] == 0 and fake.logged == []
assert client.get("/api/case/M-1004-20261113T085225Z-000000").status_code == 404
assert fake.logged == []
assert client.get(f"/api/case/{CID}").json()["status"] == "review"
assert fake.logged == [(CID, "M-1004")]

fake.log_fail = True
r = client.get(f"/api/case/{CID}")
assert r.status_code == 503 and "review" not in r.text

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

# --- assess
fake, t, client = build()
assert client.get("/api/assess").status_code == 405
for body in [{"member_id": "M-9999"}, {}, {"member_id": ["M-1001"]}]:
    assert client.post("/api/assess", json=body).status_code == 400
assert client.post("/api/assess", content=b"{not json").status_code == 400
assert client.post("/api/assess", content=b"x" * 5000).status_code == 413
assert fake.calls["slot"] == 0 and fake.calls["assess"] == 0

r = client.post("/api/assess", json={"member_id": "M-1001"})
assert r.status_code == 200 and r.json()["result"]["governance"] == "synced"
assert r.json()["usage"]["allowed"] is True and fake.calls["assess"] == 1

fake.assess_fail = True
r = client.post("/api/assess", json={"member_id": "M-1001"})
assert r.status_code == 502 and "manager down" not in r.text and "usage" in r.json()

fake.assess_fail, fake.slots = False, 0
before = fake.calls["assess"]
r = client.post("/api/assess", json={"member_id": "M-1001"})
assert r.status_code == 429 and fake.calls["assess"] == before

# --- decide
fake, t, client = build()
ok = {"case_id": CID, "decisions": {"0": "confirm"}, "note": " fine "}
r = client.post("/api/decide", json=ok)
assert r.status_code == 200 and r.json()["outcome"] == "confirmed"
assert fake.decided == [(CID, {"0": "confirm"}, "demo reviewer", "fine")]

fake.decided.clear()
for body in [{"case_id": "x"}, {**ok, "decisions": {"a": "confirm"}}, {**ok, "note": "n" * 501}]:
    assert client.post("/api/decide", json=body).status_code == 400
assert client.post("/api/decide", content=b"nope").status_code == 400
assert fake.decided == []

fake.decide_error = ValueError("note is required when dismissing a finding")
r = client.post("/api/decide", json=ok)
assert r.status_code == 400 and "note is required" in r.json()["error"]
fake.decide_error = KeyError("no such case")
assert client.post("/api/decide", json=ok).status_code == 404
fake.decide_error = RuntimeError("secret detail")
r = client.post("/api/decide", json=ok)
assert r.status_code == 500 and "secret detail" not in r.text
# Cloud Run reserves paths ending in z (e.g. /healthz) on run.app URLs.
assert not [r.path for r in make_app(Fake()).routes if r.path.rstrip("/").endswith("z")]
print("all web tests passed")
