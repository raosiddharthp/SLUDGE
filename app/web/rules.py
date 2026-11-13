"""Input rules for the public API. Pure, so they test offline."""
import re

LENSES = ("overdraft", "vetter", "escalade", "paisawala", "redact", "ledger", "trustwell")
# Exactly the shape store.save_case generates. Anything else never reaches Firestore.
CASE_ID = re.compile(r"^M-\d{4}-\d{8}T\d{6}Z-[0-9a-f]{6}$")

MEMBERS = ("M-1001", "M-1002", "M-1003", "M-1004", "M-1005")  # synthetic members only
MAX_NOTE = 500
MAX_REVIEWER = 40
DEFAULT_REVIEWER = "demo reviewer"


def clean_member(body):
    member = body.get("member_id") if isinstance(body, dict) else None
    if member not in MEMBERS:
        raise ValueError("unknown member")
    return member


def clean_decide(body):
    """Validate a public decide request. Returns (case_id, decisions, reviewer, note) or raises ValueError."""
    if not isinstance(body, dict):
        raise ValueError("expected a JSON object")
    case_id = body.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID.match(case_id):
        raise ValueError("invalid case id")
    raw = body.get("decisions") or {}
    if (not isinstance(raw, dict) or len(raw) > 10
            or not all(isinstance(k, str) and k.isdigit() and isinstance(v, str) for k, v in raw.items())):
        raise ValueError("decisions must map a finding number to confirm or dismiss")
    reviewer = str(body.get("reviewer") or "").strip()[:MAX_REVIEWER] or DEFAULT_REVIEWER
    note = str(body.get("note") or "").strip()
    if len(note) > MAX_NOTE:
        raise ValueError(f"note is limited to {MAX_NOTE} characters")
    return case_id, raw, reviewer, note
