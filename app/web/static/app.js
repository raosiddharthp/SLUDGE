"use strict";

const $ = (id) => document.getElementById(id);
const MEMBERS = ["M-1001", "M-1002", "M-1003", "M-1004", "M-1005"];
const DRIVERS = { life_events: "Life event", health: "Health", resilience: "Financial resilience", capability: "Capability" };
const SOURCES = { crm: "Contact centre", app: "Member app", core: "Core banking" };
const SIGNALS = {
  insufficient_data: "Too few decisions yet to judge reviewer behaviour.",
  rubber_stamp_risk: "Red flag: nothing has been dismissed. Reviewers may be rubber-stamping.",
  ok: "Reviewers are dismissing some findings, which is a healthy sign.",
};

let selected = null;
let remaining = 1;

function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const kid of kids.flat(Infinity)) if (kid !== null && kid !== undefined) node.append(kid);
  return node;
}

function say(message, kind = "info") {
  const bar = $("status");
  bar.className = "status " + kind;
  bar.textContent = message;
}

async function api(path, body) {
  const options = body === undefined ? {}
    : { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, options);
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON error body */ }
  if (!res.ok) {
    const err = new Error((data && data.error) || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function when(iso) {
  const d = new Date(iso);
  return isNaN(d) ? "" : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
const label = (map, key) => map[key] || key;
const sourceOf = (unitId) => label(SOURCES, String(unitId).split(":")[0]);
const textOf = (item) => (typeof item === "string" ? item : (item && (item.text || item.action || item.quote)) || JSON.stringify(item));

/* ---------- queue, usage, override ---------- */

async function loadQueue() {
  const { queue } = await api("/api/queue");
  const list = $("queue-list");
  list.replaceChildren();
  if (!queue.length) list.append(el("p", { class: "empty", text: "Nothing is waiting for review." }));
  for (const row of queue) {
    const item = el("button", { type: "button", class: "q-item" + (row.case_id === selected ? " selected" : "") },
      el("span", { class: "pill " + row.urgency, text: row.urgency }),
      el("span", { class: "q-member", text: row.member_id }),
      el("span", { class: "q-headline", text: row.headline }),
      el("span", { class: "q-time", text: when(row.created_at) }));
    item.addEventListener("click", () => openCase(row.case_id));
    list.append(item);
  }
}

function showUsage(u) {
  remaining = u.remaining;
  $("usage").textContent = `${u.remaining} of ${u.cap} assessments left today (resets 00:00 UTC). Each one calls Gemini and costs well under a cent.`;
  $("assess").disabled = remaining <= 0;
}
const loadUsage = async () => showUsage(await api("/api/usage"));

async function loadOverride() {
  const o = await api("/api/override");
  const pct = o.rate === null ? "n/a" : `${Math.round(o.rate * 100)}%`;
  $("override").replaceChildren(
    el("strong", { text: `Override rate ${pct}` }),
    ` (${o.overridden} dismissed of ${o.decided_findings} decided). `,
    SIGNALS[o.signal] || "");
}

async function refreshAll() {
  try {
    await Promise.all([loadQueue(), loadUsage(), loadOverride()]);
    say("Up to date.");
  } catch (err) {
    say(`Could not load data: ${err.message}`, "warn");
  }
}

/* ---------- assess ---------- */

async function runAssess() {
  const member = $("member").value;
  const button = $("assess");
  button.disabled = true;
  say(`Assessing ${member}… this calls Gemini and can take up to about 30 seconds.`);
  try {
    const out = await api("/api/assess", { member_id: member });
    showUsage(out.usage);
    const status = out.result.status;
    if (status === "clean") say(`${member}: no findings. The case was closed automatically.`, "ok");
    else if (status === "queued_error") say(`${member}: the pipeline failed upstream, so the case is queued for manual review.`, "warn");
    else say(`${member}: findings verified and added to the queue.`, "ok");
    await Promise.all([loadQueue(), loadOverride()]);
  } catch (err) {
    if (err.status === 429) {
      showUsage(err.data.usage);
      say("Today's assessment allowance is used up. It resets at 00:00 UTC.", "warn");
    } else {
      if (err.data && err.data.usage) showUsage(err.data.usage);
      say(`The assessment failed (${err.message}). The allowance slot was still used.`, "warn");
    }
  } finally {
    button.disabled = remaining <= 0;
  }
}

/* ---------- case view ---------- */

function evidenceBlock(e) {
  return el("figure", { class: "evidence" },
    el("blockquote", { class: "quote", text: e.quote }),
    el("figcaption", { class: "source" }, `${sourceOf(e.unit_id)} · `, el("code", { text: e.unit_id })));
}

function choiceRow(index, choices) {
  const row = el("div", { class: "choices", role: "group", "aria-label": `Decision for finding ${index + 1}` });
  for (const value of ["confirm", "dismiss"]) {
    const button = el("button", { type: "button", class: `choice ${value}`, "aria-pressed": "false", text: value === "confirm" ? "Confirm" : "Dismiss" });
    button.addEventListener("click", () => {
      choices[index] = value;
      for (const b of row.children) {
        const on = b.classList.contains(value);
        b.classList.toggle("active", on);
        b.setAttribute("aria-pressed", String(on));
      }
    });
    row.append(button);
  }
  return row;
}

function findingCard(entry, index, choices) {
  const f = entry.finding;
  const card = el("article", { class: "finding" },
    el("div", { class: "finding-head" },
      el("strong", { text: label(DRIVERS, f.driver) }),
      el("span", { class: "chip", text: `confidence ${Math.round(f.confidence * 100)}%` }),
      f.repeat_disclosure ? el("span", { class: "chip warn", text: "repeat disclosure" }) : null),
    el("p", { class: "rationale", text: f.rationale }),
    (f.evidence || []).map(evidenceBlock),
    (entry.notes || []).map((n) => el("p", { class: "gate-note", text: `Gate adjustment: ${n}` })));
  if (choices) card.append(choiceRow(index, choices));
  return card;
}

function recommendationBlock(rec) {
  return el("div", { class: "recommendation" },
    el("strong", { text: rec.headline }),
    el("ul", {}, (rec.actions || []).map((a) => el("li", { text: textOf(a) }))));
}

function decisionForm(c, choices) {
  const accepted = c.accepted || [];
  const note = el("textarea", { id: "note", rows: "3", maxlength: "500",
    placeholder: accepted.length ? "Required if you dismiss any finding. Say why." : "Required: say how this case was handled." });
  const reviewer = el("input", { id: "reviewer", type: "text", maxlength: "40", placeholder: "demo reviewer" });
  const submit = el("button", { type: "button", class: "btn primary", text: accepted.length ? "Submit decision" : "Acknowledge case" });
  submit.addEventListener("click", async () => {
    if (accepted.length && Object.keys(choices).length !== accepted.length) {
      say("Decide every finding first: choose Confirm or Dismiss on each one.", "warn");
      return;
    }
    const dismissing = Object.values(choices).includes("dismiss");
    if ((dismissing || !accepted.length) && !note.value.trim()) {
      say("A note is required for this decision.", "warn");
      return;
    }
    submit.disabled = true;
    try {
      const out = await api("/api/decide", { case_id: c.case_id, decisions: choices, reviewer: reviewer.value, note: note.value });
      say(`Decision recorded: ${out.outcome}.`, "ok");
      await Promise.all([loadQueue(), loadOverride()]);
      await openCase(c.case_id);
    } catch (err) {
      say(err.message, "warn");
      submit.disabled = false;
    }
  });
  return el("div", { class: "decision" },
    el("div", {}, el("label", { for: "reviewer", text: "Reviewer name (optional)" }), reviewer),
    el("div", {}, el("label", { for: "note", text: "Note" }), note),
    el("div", {}, submit));
}

function decidedSummary(c) {
  const rows = (c.decisions || []).map((d) => el("li", { text: `Finding ${d.index + 1} (${label(DRIVERS, d.driver)}): ${d.decision}` }));
  return el("div", { class: "decided" },
    el("strong", { text: `Decided: ${c.outcome} by ${c.reviewer}` }),
    el("span", { text: ` · ${when(c.decided_at)}` }),
    rows.length ? el("ul", {}, rows) : null,
    c.review_note ? el("p", { text: `Note: ${c.review_note}` }) : null);
}

function renderCase(c) {
  const panel = $("case");
  const pending = c.review_state === "pending";
  const accepted = c.accepted || [];
  const rejected = c.rejected || [];
  const choices = pending ? {} : null;
  const parts = [
    el("div", { class: "case-head" },
      el("h2", { text: c.member_id }),
      el("span", { class: "chip", text: c.status }),
      el("span", { class: "chip", text: c.review_state })),
    el("p", { class: "meta" }, el("code", { text: c.case_id }), ` · assessed ${when(c.created_at)} · model ${c.model || "n/a"}`),
    c.note ? el("p", { class: "model-note", text: `Model note: ${c.note}` }) : null,
    c.recommendation ? [el("h3", { text: "Recommendation" }), recommendationBlock(c.recommendation)] : null,
    el("h3", { text: "Findings the system verified" }),
    accepted.length ? accepted.map((entry, i) => findingCard(entry, i, choices))
      : el("p", { class: "empty", text: "No verified findings." }),
    rejected.length ? [el("h3", { text: "Rejected by the grounding gates" }),
      rejected.map((r) => el("div", { class: "rejected", text: `${label(DRIVERS, r.finding.driver)}: ${(r.reasons || []).join("; ")}` }))] : null,
    pending ? decisionForm(c, choices) : decidedSummary(c),
  ];
  panel.replaceChildren(...parts.flat(Infinity).filter((part) => part !== null && part !== undefined));
}

async function openCase(id) {
  selected = id;
  try {
    renderCase(await api(`/api/case/${encodeURIComponent(id)}`));
    await loadQueue();
  } catch (err) {
    say(`Could not open the case: ${err.message}`, "warn");
  }
}

function init() {
  for (const m of MEMBERS) $("member").append(el("option", { value: m, text: m }));
  $("assess").addEventListener("click", runAssess);
  $("refresh").addEventListener("click", refreshAll);
  refreshAll();
}
init();
