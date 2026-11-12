"""Run Detection several times per member; report driver stability and quote grounding."""
import argparse
import collections
import json
import os
import time

from app.agents.detection.detector import detect
from app.agents.ingest.sources import fetch_bundle
from app.common.records import index_records

MEMBERS = ["M-1001", "M-1002", "M-1003", "M-1004", "M-1005"]


def bad_quotes(bundle, findings):
    """Count quotes that are not an exact substring of the cited record."""
    idx = index_records(bundle)
    bad = 0
    for f in findings:
        for e in f["evidence"]:
            rec = idx.get(e["unit_id"])
            if rec is None or e["quote"] not in rec["text"]:
                bad += 1
    return bad


def one_call(bundle):
    out = detect(bundle)
    if "error" in out:
        time.sleep(5)
        out = detect(bundle)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    model = os.environ.get("SLUDGE_MODEL", "gemini-3.5-flash-lite")
    report = {}
    for member_id in MEMBERS:
        bundle = fetch_bundle(member_id)
        drivers = collections.Counter()
        conf = collections.defaultdict(list)
        ok = errors = bad = tok_in = tok_out = 0
        for _ in range(args.runs):
            out = one_call(bundle)
            if "error" in out:
                errors += 1
                continue
            ok += 1
            findings = out["result"]["findings"]
            bad += bad_quotes(bundle, findings)
            tokens = out.get("tokens") or {}
            tok_in += tokens.get("in") or 0
            tok_out += tokens.get("out") or 0
            for d in {f["driver"] for f in findings}:
                drivers[d] += 1
            for f in findings:
                conf[f["driver"]].append(f["confidence"])
            time.sleep(1)
        report[member_id] = {
            "ok": ok,
            "errors": errors,
            "drivers": dict(drivers),
            "mean_confidence": {d: round(sum(v) / len(v), 2) for d, v in conf.items()},
            "bad_quotes": bad,
            "tokens": {"in": tok_in, "out": tok_out},
        }
        seen = ", ".join(f"{d} {n}/{ok}" for d, n in sorted(drivers.items())) or "none"
        print(f"{member_id}: ok={ok} err={errors} bad_quotes={bad} drivers: {seen}")
    path = os.path.join("app", "eval", f"results_{model}.json")
    with open(path, "w") as fh:
        json.dump({"model": model, "runs": args.runs, "members": report}, fh, indent=2)
    print("saved", path)


if __name__ == "__main__":
    main()
