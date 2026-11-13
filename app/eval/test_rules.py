from datetime import datetime, timedelta, timezone

from app.web.audit import entry
from app.web.rules import clean_decide, clean_member

CID = "M-1004-20261113T085225Z-e7516f"


def rejects(fn, arg):
    try:
        fn(arg)
    except ValueError:
        return True
    return False


assert clean_member({"member_id": "M-1001"}) == "M-1001"
for bad in [None, {}, {"member_id": "M-9999"}, {"member_id": "M-1001; DROP"}, [], "M-1001"]:
    assert rejects(clean_member, bad), bad

ok = {"case_id": CID, "decisions": {"0": "confirm"}, "reviewer": "  Ann  ", "note": " fine "}
assert clean_decide(ok) == (CID, {"0": "confirm"}, "Ann", "fine")
assert clean_decide({"case_id": CID, "decisions": {"0": "dismiss"}, "note": "n"})[2] == "demo reviewer"
assert len(clean_decide({**ok, "reviewer": "x" * 100})[2]) == 40
assert clean_decide({"case_id": CID})[1] == {}

for bad in [None, [], {"case_id": "x"}, {"case_id": 5}, {**ok, "decisions": ["confirm"]},
            {**ok, "decisions": {"a": "confirm"}}, {**ok, "decisions": {"0": 1}},
            {**ok, "decisions": {str(i): "confirm" for i in range(11)}}, {**ok, "note": "n" * 501}]:
    assert rejects(clean_decide, bad), bad

now = datetime(2026, 11, 13, 9, 5, 42, tzinfo=timezone.utc)
doc_id, doc = entry(CID, "M-1004", now)
assert doc_id == f"{CID}-20261113T0905"
assert entry(CID, "M-1004", now.replace(second=5))[0] == doc_id
assert entry(CID, "M-1004", now.replace(minute=6))[0] != doc_id
assert doc["actor"] == "public-demo" and doc["retain_until"] - doc["at"] == timedelta(days=90)
assert set(doc) == {"case_id", "member_id", "actor", "action", "at", "retain_until"}
print("all rules tests passed")
