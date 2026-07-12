# SLUDGE

**S**ystem for **L**ocating **U**nseen **D**isclosures, **G**aps & **E**xposure

A Consumer Duty outcomes copilot built for a fictional UK retail mutual — designed to answer one question a real 2024–2026 FCA enforcement pattern keeps asking every UK financial services firm: *if you're only reviewing 2% of customer interactions, what's your evidence for the other 98%?*

[Design Document](./index.html) · [Architecture](#architecture) · [ADRs](#key-design-decisions) · [Status](#status)

---

## The problem, in one sentence

Old Street Mutual's contact centre manually QA-samples ~2% of customer interactions to evidence fair treatment under FCA Consumer Duty. The FCA's own April 2026 findings say that's no longer defensible — a sample that small cannot show good outcomes occur consistently for everyone else. SLUDGE closes that gap: not by reviewing faster, but by reviewing *everything*, and surfacing only what a human actually needs to act on.

This isn't a hypothetical risk framed for a pitch deck. In 2024 alone, real UK firms were fined **£176m+** in aggregate FCA enforcement, with three separate penalties specifically for unfair treatment of customers in financial difficulty — TSB (£10.9m fine, £99.9m redress), HSBC (£6.28m fine, £185m redress), and Volkswagen Financial Services (£5.4m fine, £21.5m redress). Full citations in the [design document](./index.html#s5).

## What SLUDGE does

Five bounded agents, one governed dataset, a human at every gate:

```
Ingest ──▶ Detection ──▶ Manager ──▶ Escalation ──▶ Governance
(Paisawala) (Vetter)    (Trustwell)  (Escalade)     (Overdraft/Ledger)
                             │
                             └──▶ Human Review Queue
                                  (timeout · low-confidence · failed-grounding)
```

- **Ingest Agent** — read-only connectors against existing systems (app, CRM, core banking). No schema changes, no new system for anyone to maintain.
- **Detection Agent** — classifies each interaction against the FCA's four FG21/1 vulnerability drivers (health, life events, resilience, capability), using Gemini structured output. Every claim ships with a cited evidence span — a transaction date, a transcript line — not just a confidence score.
- **Manager Agent** — the runtime authority, not a passthrough orchestrator. Enforces a hard grounding gate as an explicit state machine: `Ungrounded → Grounded` or `Ungrounded → Failed-Grounding → Routed-to-Human-Queue`. Nothing ungrounded reaches a human as if it were settled fact.
- **Escalation Agent** — drafts a plain-language next-best-action, surfaced mid-call, not after.
- **Governance Agent** — runs in parallel, not inline. Rolls the same underlying dataset into seven role-specific lenses (Chairman, Compliance, Contact Centre, Data, DPO, Finance, Risk), each with the *type* of explainability that role actually needs — evidential, systemic, procedural, or behavioural. One dataset, not seven dashboards.

The existing 2% manual QA process is never switched off. It's repositioned — from primary evidencing mechanism to deep-dive validation layer — once full coverage is live.

## Key design decisions

Ten ADRs, each with a rejected alternative — full detail in [§10 of the design document](./index.html#s10):

| ADR | Decision | Rejected because |
|---|---|---|
| 01 | Read-only augmentation | A canonical schema-first rebuild inherits the exact integration risk it's meant to fix |
| 02 | Gemini structured output over a fine-tuned classifier | Can't produce a human-readable rationale without a bolted-on explanation layer |
| 03 | Single combined HITL review | Two-stage flag/action approval doesn't match how vulnerability response actually works in practice |
| 04 | One dataset, seven role-based lenses | Per-stakeholder dashboards recreate exactly the governance sprawl this project is scoped to avoid |
| 07 | Five bounded agents, not one monolithic call | A single call flattens four distinct stakeholder ownership boundaries into one artefact nobody owns |
| 08 | A Manager Agent with real runtime authority | Sequencing without accountability is the same failure this whole decision exists to prevent |
| 09 | Explainability is tiered by role, not one report | A transcript citation means nothing to a Finance Director; a methodology writeup means nothing to a contact-centre agent mid-call |

## Architecture

Full C4 context, container, and component diagrams — plus the layered view (Presentation → Agent Orchestration → ML/Intelligence → Data → API boundary → Infrastructure, with Governance & Security and Observability as cross-cutting bands) — live in the [design document, §7](./index.html#s7).

**Stack:** Google Cloud · Gemini (structured output) · agent boundaries mapped 1:1 to stakeholder ownership, not task convenience.

## Grounded, not hand-waved

Every number in this repo that looks like a fact is either cited to a real, named source or explicitly labelled as an illustrative estimate with its method shown:

- Real precedent: FCA 2024 enforcement actions (TSB, HSBC, Volkswagen Financial Services), the FCA's own April 2026 "beyond MI dashboards" finding, and the FCA Financial Lives Survey's 49% national vulnerability characteristic rate — all cited in [§5](./index.html#s5).
- Illustrative: Old Street Mutual's own £18m revenue and £2.0–2.6m non-compliance exposure are modelled from two real ratios (a comparable building society's asset-per-member figure, HSBC's actual fine-multiplier methodology) with the assumption stated at every step — never presented as fact.

## Who this is built for

Eleven named people, not an abstract user base — a Chairman personally accountable under SM&CR, a Compliance Head who inherited a 2% sample she can't fully stand behind, a DPO who redacts first and asks questions second, four customers whose current failures the existing systems can't see. Full persona register in [§2](./index.html#s2). Every architecture decision in this repo traces back to one of them — see the [traceability matrix](./index.html#s10).

## Status

This repository currently contains the **living design document** — client brief through architecture, ADRs, cost analysis, roadmap, and a scripted five-agent pipeline simulation. The design document's simulator is intentionally **scripted and animated**, not a live model call — no API key is embedded in a static, shareable HTML file. A real Gemini-backed implementation is a separate, later build.

| | |
|---|---|
| Design document | ✅ Complete — 14 sections, 10 ADRs, full traceability |
| Working application | ⏳ Not yet started |
| Deployment | Not yet decided — deliberately, rather than inheriting a pattern from an unrelated project |

## Disclaimer

Old Street Mutual, Lord Overdraft, SLUDGE, and every named stakeholder and customer persona in this repository are fictional constructs built for a portfolio piece. All regulatory references — FCA Consumer Duty, FG21/1, GDPR/ICO, and the enforcement precedent cited throughout — describe real, cited UK frameworks and real 2024 FCA actions. The company and characters applying them do not exist.

---

<sub>Built as a Google Cloud Applied AI Customer Engineer portfolio piece — demonstrating Consumer Duty domain fluency, agent-boundary architecture judgment, and pre-sales narrative discipline end to end, from client brief to a presentation-ready stakeholder deck.</sub>
