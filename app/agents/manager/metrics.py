"""Override rate: how often reviewers dismiss what the system recommended."""
MIN_SAMPLE = 10  # below this many decided findings, the rate says nothing


def override_rate(cases):
    decided = overridden = 0
    for c in cases:
        for d in c.get("decisions") or []:
            decided += 1
            overridden += d["decision"] == "dismiss"
    rate = overridden / decided if decided else None
    if decided < MIN_SAMPLE:
        signal = "insufficient_data"
    elif overridden == 0:
        signal = "rubber_stamp_risk"
    else:
        signal = "ok"
    return {"decided_findings": decided, "overridden": overridden, "rate": rate, "signal": signal}
