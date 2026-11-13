# SLUDGE developer guide

SLUDGE is a Consumer Duty outcomes copilot for a fictional UK building society, Old Street Mutual. It is a portfolio proof of concept. All data is synthetic. The design rationale is in the [design doc](https://raosiddharthp.github.io/SLUDGE/), and this file covers how the code is built, run, tested and deployed.

## Architecture

The system is hub-and-spoke (ADR-08, ADR-11). The Manager is the only agent that calls other agents.

```
reviewer UI ──> sludge-web (public) ──> sludge-manager
                                           │
              ┌────────────────┬───────────┴──────────┬──────────────────┐
              ▼                ▼                      ▼                  ▼
        sludge-ingest   sludge-detection      sludge-escalation   sludge-governance
                        (Gemini, LLM)         (rules)             (rules, BigQuery sync)
```

- **Manager** runs Ingest, then Detection, then the citation gates, then Escalation. Each stage gets one retry with a 4 second backoff. After the case is saved, it calls Governance with a bounded 25 second wait.
- **Detection** is the only agent that calls a model (Gemini 3.5 Flash-Lite). The gates check that citations exist, not that they mean what the model claims.
- **Escalation and Governance** are deterministic rules. The design doc describes them as model agents, and the as-built note in section 12 records the difference.
- **Web** serves the reviewer UI and the Governance lens page. After a reviewer decision it triggers a Governance sync with a bounded 10 second wait.
- Agents talk over A2A using Google ADK (`google-adk[a2a]`). Each agent is a custom `BaseAgent` wrapped with `to_a2a`. Private services require Google ID tokens, and `call_agent(url, text, timeout=60)` in `app/common/a2a_client.py` handles that.

The Governance sync is a bounded wait rather than a parallel call because Cloud Run throttles CPU once a request has returned.

## Repository layout

| Path | Purpose |
| --- | --- |
| `app/agents/ingest`, `detection`, `escalation`, `governance`, `manager` | One folder per agent. Each has an `agent.py` that exposes the A2A app. |
| `app/agents/manager/` | Orchestration (`orchestrate.py`), gates, decisions, the queue (`queue.py`), the store (`store.py`) and the Governance trigger (`govern.py`). |
| `app/agents/governance/` | `flatten.py` and `sync.py` write BigQuery tables. `lenses.sql` defines the seven views. |
| `app/common/` | A2A client, usage cap, record types and probes. |
| `app/web/` | Starlette app (`server.py`), data access (`data.py`), lens cache (`cache.py`), audit log (`audit.py`) and the static UI. |
| `app/eval/` | Gold set, replay tool and the offline tests (`test_*.py`). |
| `app/data/` | Synthetic data and the Firestore seeder. |
| `Dockerfile`, `.gcloudignore` | One image runs every service. |

## Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `SLUDGE_AGENT` | all agents | Which agent module the image starts. |
| `SLUDGE_APP` | any service | Overrides the default ASGI app path in the Dockerfile `CMD`. |
| `SLUDGE_STORE` | manager | Set to `firestore` to save cases to Firestore. Read in `app/agents/manager/agent.py`. |
| `A2A_HOST`, `A2A_PORT`, `A2A_PROTOCOL` | agents | How an agent advertises itself. |
| `SLUDGE_INGEST_URL`, `SLUDGE_DETECTION_URL`, `SLUDGE_ESCALATION_URL`, `SLUDGE_GOVERNANCE_URL` | manager | Addresses of the other agents. |
| `SLUDGE_MANAGER_URL` | web | Address of the Manager. |
| `SLUDGE_GOVERNANCE_URL` | web | Address of Governance, for the sync after a decision. |

Never print or commit the Gemini key. Keep secrets out of terminal output you share.

## Run the tests

The tests are standalone modules under `app/eval/` and need no network or cloud access. Run one with:

```bash
python -m app.eval.test_web
```

Run all of them:

```bash
for f in app/eval/test_*.py; do
  m=$(basename "$f" .py)
  python -m app.eval.$m >/dev/null 2>&1 && echo "ok   $m" || echo "FAIL $m"
done
```

The web tests also enforce the UI rules: no `innerHTML`, no inline scripts and a strict Content Security Policy.

## Data stores

**Firestore** (the default database, shared with the Lumen demo). Collections carry the `sludge_` prefix.

| Collection | Contents | Expiry |
| --- | --- | --- |
| `sludge_cases` | One document per assessment. | TTL on `retain_until`. |
| `sludge_usage` | Daily usage counters for the cap. | None. |
| `sludge_access_log` | Who opened which case. | TTL on `retain_until`. |

Seven early cases predate `retain_until`. They never expire, and the Redact lens shows them as "not recorded".

TTL deletes are billed and can run up to about 24 hours after the expiry time.

**BigQuery** dataset `sludge_gov` (`us-east1`). The sync rewrites three tables in full on each run: `cases`, `findings` and `access_log`. Seven views, one per lens, sit on top: `lens_overdraft`, `lens_vetter`, `lens_escalade`, `lens_paisawala`, `lens_redact`, `lens_ledger` and `lens_trustwell`. `AT` is a reserved word, so the access time column is `viewed_at`.

## Web service

| Endpoint | Behaviour |
| --- | --- |
| `GET /`, `GET /static/*` | The reviewer UI and the Governance page. |
| `GET /health` | Health check. Cloud Run reserves paths ending in `z`, so `/healthz` does not work. |
| `GET /api/queue` | Pending cases. See the queue rules below. |
| `GET /api/case/{id}` | One case. It writes an access log entry first and returns 503 if it cannot. |
| `GET /api/lens/{name}` | One of the seven lenses. Queries cap at 100 MB billed, and results are cached for 5 minutes per instance. |
| `GET /api/override`, `GET /api/usage` | Override rate and daily usage. |
| `POST /api/assess` | Runs an assessment. Members M-1001 to M-1005 only, 20 a day, 429 beyond that. |
| `POST /api/decide` | Records a decision. The body limit is 4 KB. |

**Queue rules.** Each member's newest case is taken first, in any state. It is shown only if it is still pending, so an older pending case never resurfaces after a newer one is decided.

**Override rate.** Dismissals divided by decided findings. Below 10 decided findings the signal is `insufficient_data`. Above that it is `rubber_stamp_risk` or `ok`.

**Lens cache.** The cache is per instance and clears after a successful assess or decide on that instance. A different instance can serve data up to 5 minutes old. Check BigQuery before assuming the sync failed.

**Scale note.** The queue reads every case document on each refresh, up to about 1,800 reads in the worst case. That is fine at demo traffic. For more, replace it with an indexed per-member query.

## Deploy

All services run in `us-east1` in the project `lumen-poc-srao26`, from one image: `us-east1-docker.pkg.dev/lumen-poc-srao26/sludge/agents:vN`. Only `sludge-web` is public.

1. Build and push a new version. This takes about a minute:

   ```bash
   gcloud builds submit --tag us-east1-docker.pkg.dev/lumen-poc-srao26/sludge/agents:vN --project=lumen-poc-srao26 .
   ```

2. Move every SLUDGE service to it. Derive the list from Cloud Run, because a list typed from memory once left Governance behind:

   ```bash
   for s in $(gcloud run services list --project=lumen-poc-srao26 --region=us-east1 --filter="metadata.name~sludge" --format="value(metadata.name)"); do
     gcloud run deploy "$s" --image=us-east1-docker.pkg.dev/lumen-poc-srao26/sludge/agents:vN --region=us-east1 --project=lumen-poc-srao26 --quiet
   done
   ```

3. Confirm every service reports the new image, then delete the superseded version. Each version adds about 44 MB, and the free tier is 0.5 GB.

`.gcloudignore` patterns without a leading slash match at any depth. Anchor root-only rules, as in `/index.html`. An unanchored rule once dropped `app/web/static/index.html` from the image.

## Cost and constraints

- Each project has a billing cap of about one cent, so keep usage low and keep the daily cap in place.
- Do not disable projects or unlink billing.
- SLUDGE shares `lumen-poc-srao26` with the Lumen demos, so keep the `sludge` and `sludge_` prefixes.
- Measured cost is about $0.0006 to $0.0007 per assessed case.
- Use synthetic data only.
