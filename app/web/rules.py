"""Input rules for the public API. Pure, so they test offline."""
import re

LENSES = ("overdraft", "vetter", "escalade", "paisawala", "redact", "ledger", "trustwell")
# Exactly the shape store.save_case generates. Anything else never reaches Firestore.
CASE_ID = re.compile(r"^M-\d{4}-\d{8}T\d{6}Z-[0-9a-f]{6}$")
