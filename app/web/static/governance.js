"use strict";

const LENSES = [
  { name: "overdraft", persona: "Overdraft", question: "Are we looking at every member, and can each flag be traced back to its evidence?",
    cols: [["day", "Day"], ["cases", "Cases"], ["members_assessed", "Members assessed"], ["coverage_pct", "Coverage %"],
           ["flagged_cases", "Flagged cases"], ["flagged_drillable", "Drillable"], ["drillthrough_pct", "Drill-through %"]] },
  { name: "vetter", persona: "Vetter", question: "What did the system find, and what did the reviewer decide?",
    cols: [["created_at", "Created"], ["case_id", "Case"], ["member_id", "Member"], ["status", "Status"], ["review_state", "Review state"],
           ["outcome", "Outcome"], ["driver", "Driver"], ["grounded", "Grounded"], ["confidence", "Confidence"],
           ["decision", "Decision"], ["reviewer", "Reviewer"], ["review_note", "Note"]] },
  { name: "escalade", persona: "Escalade", question: "Are the findings grounded in the source record?",
    cols: [["day", "Day"], ["findings_total", "Findings"], ["grounded", "Grounded"], ["grounding_pass_pct", "Pass %"], ["meets_target", "Meets target"]] },
  { name: "paisawala", persona: "Paisawala", question: "Is the pipeline reliable, and where does it need retries?",
    cols: [["day", "Day"], ["cases", "Cases"], ["cases_with_retries", "Cases with retries"], ["failed_attempts", "Failed attempts"],
           ["queued_errors", "Queued errors"], ["queued_error_pct", "Queued error %"]] },
  { name: "redact", persona: "Redact", question: "How long do we keep each case, and who has looked at it?",
    cols: [["created_at", "Created"], ["case_id", "Case"], ["member_id", "Member"], ["lawful_basis", "Lawful basis"], ["retain_until", "Retain until"],
           ["days_remaining", "Days left"], ["retention_state", "Retention"], ["access_entries", "Access entries"], ["last_viewed", "Last viewed"]] },
  { name: "ledger", persona: "Ledger", question: "What does each assessment cost?",
    cols: [["day", "Day"], ["cases", "Cases"], ["members_assessed", "Members assessed"], ["tokens_in", "Tokens in"], ["tokens_out", "Tokens out"],
           ["cost_usd", "Cost (USD)"], ["cost_per_case_usd", "Cost per case (USD)"]] },
  { name: "trustwell", persona: "Trustwell", question: "Are reviewers weighing each finding or rubber-stamping, and is the model's confidence drifting?",
    cols: [["day", "Day"], ["decided", "Decided"], ["overridden", "Overridden"], ["override_rate", "Override rate"], ["override_signal", "Signal"],
           ["avg_confidence", "Avg confidence"], ["confidence_drift", "Confidence drift"], ["drift_flag", "Drift flag"]] },
];

function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  node.append(...kids.flat(Infinity).filter((k) => k !== null && k !== undefined && k !== false));
  return node;
}

function fmt(v) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : String(Math.round(v * 10000) / 10000);
  if (typeof v === "object") return JSON.stringify(v);
  const s = String(v);
  return /^\d{4}-\d{2}-\d{2}T/.test(s) ? s.slice(0, 16).replace("T", " ") : s;
}

function table(rows, cols) {
  const head = el("tr", {}, cols.map(([, label]) => el("th", { scope: "col" }, label)));
  const body = rows.map((row) => el("tr", {}, cols.map(([key]) => el("td", {}, fmt(row[key])))));
  return el("table", { class: "lens-table" }, el("thead", {}, head), el("tbody", {}, body));
}

function section(spec) {
  const status = el("p", { class: "hint", role: "status" }, "Loading…");
  const holder = el("div", { class: "tbl-wrap" });
  const node = el("section", { class: "lens", "aria-labelledby": "lens-" + spec.name },
    el("h2", { id: "lens-" + spec.name, class: "col-title" }, spec.persona),
    el("p", { class: "lens-q" }, spec.question), status, holder);
  return { node, status, holder };
}

async function fetchRows(name) {
  const res = await fetch("/api/lens/" + name, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();
  return Array.isArray(data) ? data : (data.rows || data.data || []);
}

async function fill(spec, parts) {
  try {
    const rows = await fetchRows(spec.name);
    if (!rows.length) { parts.status.textContent = "No rows yet."; return; }
    parts.status.textContent = "Latest " + rows.length + " row" + (rows.length === 1 ? "" : "s") + ".";
    parts.holder.replaceChildren(table(rows, spec.cols));
  } catch (err) {
    parts.status.textContent = "Could not load this lens. Try again in a minute.";
  }
}

function init() {
  const root = document.getElementById("lenses");
  const built = LENSES.map((spec) => ({ spec, parts: section(spec) }));
  root.replaceChildren(...built.map((b) => b.parts.node));
  built.forEach((b) => fill(b.spec, b.parts));
}

init();
