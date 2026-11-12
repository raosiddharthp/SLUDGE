"""Escalation rules: turn verified findings into a plain-language recommendation. Deterministic; no LLM."""

ACTIONS = {
    "health": ("offer_support",
               "Offer flexible support options and a specialist support conversation. "
               "Record the condition, with the member's consent, so they are not asked again."),
    "resilience": ("review_affordability",
                   "Review affordability with the member and discuss forbearance options "
                   "before any further action on the account."),
    "life_events": ("acknowledge_event",
                    "Acknowledge the life event and offer to adjust contact and payments "
                    "while the member settles."),
    "capability": ("adapt_communication",
                   "Offer a way of communicating that suits the member, and check their "
                   "understanding before any product or payment decision."),
}
LABELS = {
    "health": "health condition",
    "resilience": "money pressure",
    "life_events": "major life event",
    "capability": "difficulty understanding or managing money",
}
RECORD_ONCE = ("Add the disclosure to the member's record so they are not asked to repeat it. "
               "This member has already had to repeat themselves.")


def recommend(case):
    """Build a recommendation from a Manager case. Refuses anything unverified or ungrounded."""
    accepted = case.get("accepted") or []
    if case.get("status") != "review" or not accepted:
        raise ValueError("escalation needs a verified case with at least one accepted finding")
    findings = [a["finding"] for a in accepted]
    for f in findings:
        if not f.get("evidence"):
            raise ValueError("every finding needs cited evidence")
        if f.get("driver") not in ACTIONS:
            raise ValueError(f"unknown driver {f.get('driver')}")

    actions = []
    for i, f in enumerate(findings):
        key, text = ACTIONS[f["driver"]]
        actions.append({"findings": [i], "driver": f["driver"], "action": key, "text": text,
                        "confidence": f["confidence"]})
    repeated = [i for i, f in enumerate(findings) if f.get("repeat_disclosure")]
    if repeated:
        actions.append({"findings": repeated, "driver": None, "action": "record_once", "text": RECORD_ONCE})

    labels = list(dict.fromkeys(LABELS[f["driver"]] for f in findings))
    headline = "Possible vulnerability: " + ", ".join(labels)
    if repeated:
        headline += "; member has had to repeat themselves"
    urgency = "high" if repeated or any(f["driver"] == "health" for f in findings) else "normal"
    evidence = [{"finding": i, "unit_id": e["unit_id"], "quote": e["quote"]}
                for i, f in enumerate(findings) for e in f["evidence"]]
    return {
        "member_id": case.get("member_id"),
        "urgency": urgency,
        "headline": headline,
        "actions": actions,
        "evidence": evidence,
        "requires": "human_decision",
    }
