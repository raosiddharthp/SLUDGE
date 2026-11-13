# Lessons learned

Notes from building SLUDGE, grouped by theme. Each entry says what happened and what to do differently.

## Cloud and billing

- **A billing account has a project cap.** The number of projects you can link is limited, so plan projects before creating them.
- **Budget alerts lag.** An alert fires after the spend, so it can't protect a one-cent cap. Keep usage structurally small instead.
- **Shared Firestore prevents fine-grained IAM.** Because the default database is shared with another demo, access is granted project-wide. Use a prefix (`sludge_`) and accept the wider grant.
- **TTL deletes are billed.** They have no free quota, and they can run up to about 24 hours after expiry. Test them with a small probe collection.
- **Each image version adds about 44 MB.** The free registry tier is 0.5 GB, so delete superseded versions, and only after checking that no service uses them.
- **Cloud Run reserves paths ending in `z`.** `/healthz` never reaches your code. Use `/health`.
- **Cloud Run throttles CPU outside a request.** A background "parallel" call can stall once the response returns. A bounded wait is the reliable option.

## Agents and A2A

- **A2A 1.x uses protobuf messages.** Guides written for the 0.3 era no longer match, so read the installed SDK.
- **ADK warns about app names.** The warning is harmless, but name apps as the framework expects.
- **Use `BaseAgent` for deterministic work.** An `LlmAgent` adds a model call you don't need for rules.
- **Run `python -m uvicorn`.** A cached `uvicorn` binary can start the wrong environment.
- **httpx has a 5 second default timeout.** It bit twice. Set timeouts explicitly on every client call.
- **One retry with a backoff recovers transient failures.** A Detection read timeout recovered this way.
- **Don't rebuild the fleet list from memory.** A hand-typed loop left Governance on an old image. Derive the list from `gcloud run services list`.

## Model behaviour

- **Gemini 2.5 Flash-Lite is being retired.** Documentation pricing went stale, so check the current model and rates before costing.
- **Temperature 0 isn't deterministic.** Don't write tests that assume identical output.
- **Grounding checks verify citations, not meaning.** A finding can cite real text that doesn't support it. A human still decides.
- **Attribution can be inconsistent.** The model attributed `repeat_disclosure` differently across runs, so treat labels as advisory.
- **A dry run didn't exercise the failure path.** Test failure handling explicitly.

## Data and the web layer

- **`AT` is reserved in BigQuery.** Name the column `viewed_at`.
- **Native `replaceChildren()` doesn't flatten arrays or nulls.** Flatten before passing, or the page shows `[object HTMLHeadingElement]`.
- **`.gcloudignore` patterns match at any depth.** An unanchored `index.html` silently dropped the app's UI. Anchor root-only rules with a leading `/` and check with `gcloud meta list-files-for-upload`.
- **Decisions didn't reach the governed dataset.** They synced only on the next assessment. Trigger a bounded sync after each decision, and clear the lens cache.
- **Pick the newest case before filtering by state.** Filtering pending cases first resurfaced an older case after a newer one was decided.
- **The queue reads every case document on refresh.** That is fine at demo scale. An indexed per-member query is the scale-up path.
- **The lens cache is per instance.** Different instances can serve data up to five minutes old.

## Debugging habits

- **Verify against the source of truth before blaming a component.** Stale tables looked like a broken Governance trigger. BigQuery and the service logs showed the trigger worked, and the lens cache was the cause.
- **Don't truncate deploy output.** `tail -1` hid the revision confirmations.
- **Quote shell globs in zsh.** An unquoted `--include=*.html` fails with "no matches found".
- **A silent skip can't be measured from cases alone.** If a stage skips work without recording it, add a record before relying on a coverage metric.
- **Escalation and tier translation are rule-based here.** The design describes models. Record deviations in the design doc (see section 12) so the documents agree.
