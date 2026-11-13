import os
from datetime import datetime, timezone

from app.common.cap import DEFAULT_CAP, day_key, limit, next_count

assert next_count(0, 20) == (True, 1)
assert next_count(19, 20) == (True, 20)
assert next_count(20, 20) == (False, 20)
assert next_count(25, 20) == (False, 25)
assert next_count(0, 0) == (False, 0)

assert day_key(datetime(2026, 11, 13, 23, 59, 59, tzinfo=timezone.utc)) == "2026-11-13"
assert day_key(datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)) == "2026-11-14"

os.environ.pop("SLUDGE_DAILY_CAP", None)
assert limit() == DEFAULT_CAP
for raw, want in [("5", 5), ("0", 0), ("abc", DEFAULT_CAP), ("-3", DEFAULT_CAP)]:
    os.environ["SLUDGE_DAILY_CAP"] = raw
    assert limit() == want, (raw, limit())
print("all cap tests passed")
