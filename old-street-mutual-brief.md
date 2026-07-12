# Old Street Mutual — Customer Brief

**Consumer Duty Outcomes Copilot · Solution Train Anchor Client**

> Old Street Mutual is a fictional company invented for this portfolio piece, in the same spirit as ClaraVis Medical Systems in the Autonomous Enterprise Platform. Any resemblance to real UK financial institutions is coincidental and unintended.

---

## §1 Organisation Profile

*A member-owned high-street mutual with more heart than infrastructure — the FCA's favourite kind of firm to worry about.*

| | |
|---|---|
| **Legal name** | Old Street Mutual (Provident Society) |
| **Founded** | 1987, as a credit union for market traders around Old Street and Hoxton |
| **Structure** | Member-owned mutual, FCA-regulated (FRN fictional), not a plc — no shareholders to keep happy, which is either the whole point or the whole problem, depending who you ask |
| **Headquarters** | 1 Silicon Roundabout, Old Street, London EC1 — a building the mutual bought in 1994 for the price of a nice shed, now surrounded by fintech unicorns paying ten times the rent |
| **Members / customers** | 340,000 — mostly East London, expanding into a "digital member" base since 2019 |
| **Products** | Everyday current accounts, savings, small unsecured loans, a modest mortgage book |
| **Channels** | 4 branches, 1 contact centre (Hackney), 1 app — built by three different vendors over ten years, none of whom talk to each other |
| **Tagline** | *"Banking that remembers your name"* — increasingly hard to live up to at 340,000 members |

**The tension the whole brief hangs on:** Old Street Mutual's entire brand promise is personal, old-fashioned fairness. Its actual operating capability is a contact centre QA team that manually reviews 2% of calls. The gap between the brand promise and the evidence is exactly what the FCA's Consumer Duty rules are now forcing into the open — and exactly what your Copilot project closes.

### Regulatory Environment

| Framework | Exposure |
|---|---|
| **FCA Consumer Duty** | Full scope since 2023 (open products) and 2024 (closed back-book) — four outcomes, board-level attestation annually |
| **FCA vulnerability guidance (FG21/1)** | Baseline for all four vulnerability drivers — health, life events, resilience, capability |
| **FCA/ICO joint guidance (2026, pending)** | How to share vulnerability data across teams without breaching GDPR |
| **UK GDPR / Data Protection Act** | Special category data risk whenever a health or life-event vulnerability is disclosed |
| **SM&CR** | Named senior manager accountable for customer outcomes — currently the Chairman, somewhat to his own surprise |

---

## §2 Stakeholder Register — Internal (Business & User Profiles)

*Twelve members would be excessive for a mutual this size. Five is about right.*

**S-01 · Executive Sponsor**
**Lord Overdraft** — Chairman
*Primary concern:* His name is now, awkwardly, a genuine liability category. Lord Overdraft inherited the family estate at 24, ran it into the ground with a series of ventures best described as "confident," and was rescued from his own finances by — of all things — a mutual savings society that didn't sell him anything he didn't need. He joined the board out of gratitude, became Chairman by 60, and has spent the years since insisting, to anyone who'll listen, that Old Street Mutual "treats people the way I wish someone had treated me." Which is exactly the sentiment the FCA now wants documented, evidenced, and reported quarterly — not just felt sincerely by a well-meaning peer at the AGM.
*Question the Copilot must answer for him:* "You're telling me I can stand in front of the FCA and *prove* we treat people fairly, not just believe it?"
*Tags:* Board attestation · Consumer Duty outcomes · Reputational risk

**S-02 · Risk & Compliance**
**Ms. Miranda Vetter** — Head of Compliance
*Primary concern:* She inherited a Consumer Duty framework built mostly of spreadsheets and good intentions, and has 90 days before the next board attestation to show coverage beyond the 2% QA sample.
*Question the Copilot must answer for her:* "Show me every flagged interaction this quarter, the reasoning behind each flag, and who approved or overrode it."
*Tags:* Coverage reporting · Audit trail · HITL

**S-03 · Customer Operations**
**Mr. Desmond Cole** — Head of Contact Centre
*Primary concern:* His agents are good people who already care — what they lack is visibility across a customer's history before they pick up the phone. He does not want a system that second-guesses his team; he wants one that hands them the context they're currently missing.
*Question the Copilot must answer for him:* "Will this make my agents faster and kinder, or just add another screen they have to check?"
*Tags:* Agent workflow · Next-best-action · Adoption risk

**S-04 · Data & Technology**
**Priya Anand** — Head of Data
*Primary concern:* Three vendors, three data models, one very tired integration layer. She needs the Copilot to read across systems without becoming a fourth thing to maintain.
*Question the Copilot must answer for her:* "Does this sit above what we have, or do I have to rebuild the plumbing first?"
*Tags:* Data fabric · Augmentation not replacement · GCP architecture

**S-05 · Legal & Data Protection**
**Mr. Nigel Farr-Reaching** — Data Protection Officer
*Primary concern:* Every vulnerability signal is, potentially, special category data. He's the one who has to answer to the ICO if "helping vulnerable customers" quietly becomes "processing health data without a lawful basis."
*Question the Copilot must answer for him:* "What's the lawful basis for surfacing this, who can see it, and how long do we keep it?"
*Tags:* ICO · GDPR · Data minimisation

---

## §3 Customer Personas — The People Facing the Problem

*Four personas, one per vulnerability driver from FG21/1, so the demo dataset tells a coherent story instead of four disconnected test cases. Yes, there are Bond jokes. You asked for cheap laughs; these are load-bearing cheap laughs.*

### "Moneypenny" — Ms. Eve Moneypenny, 58
**Driver: Life events**
Recently widowed after 31 years of marriage; her late husband handled all the household finances. She's calling Old Street Mutual for the third time this month about a joint account she doesn't fully understand, using language that keeps circling back to "he always dealt with this." No missed payments yet — income and resilience are fine — but she's navigating an entirely new financial identity for the first time in three decades.
*Why she matters to the demo:* The clean "life event, no resilience issue" case — proves the Copilot doesn't just chase people already in arrears, it catches disruption before it becomes a financial problem.

### "M" — Mr. Malcolm Steel, 71
**Driver: Resilience (hidden)**
A retired quantity surveyor, proud, precise, and the last person who'd ever admit he's struggling. Two missed direct debits in six weeks. When an agent gently asked if everything was alright, he said "perfectly fine" in a tone that suggested it very much wasn't. Classic stiff-upper-lip resilience risk — disclosed nothing, and would consider being asked directly a small insult.
*Why he matters to the demo:* The "inferred, not disclosed" case. Shows the Copilot catching what a customer will never say out loud — the exact gap manual QA sampling misses, since it relies on someone flagging themselves.

### "Q" — Miss Quinta Okafor, 82
**Driver: Capability**
Whip-smart, ran a market stall for forty years, does the crossword in pen — and has failed the app's bereavement-notification journey four times because the font is too small and the language assumes a confidence with smartphones she's never needed. Everyone assumes "elderly" means "confused." Q is not confused. Q is furious that the app was clearly never tested on anyone over sixty.
*Why she matters to the demo:* Deliberately subverts the stereotype — a sharp, capable person defeated by bad design, not bad cognition. Good moment in a live demo to say explicitly: capability vulnerability is often the *product's* fault, not the customer's.

### "Dr. No" — Dr. Nadia Okonkwo-Bright, 44
**Driver: Health**
A GP, ironically, currently on extended sick leave herself following a cancer diagnosis. Income has dropped due to reduced hours; she disclosed her diagnosis to one agent in passing, months ago, and it was never logged anywhere the rest of the organisation could see. Every subsequent call has treated her as a brand-new case.
*Why she matters to the demo:* The "disclosed once, then lost" case — the single most damning gap in most firms' current process, and the cleanest example of what "coverage across the whole relationship" actually buys you.

---

## §4 Why This Cast Works for the Demo

Four personas, four drivers, four different failure modes of the *current* system — not four different failure modes of the customer:

| Persona | Driver | Current system fails because... |
|---|---|---|
| Moneypenny | Life events | No one's watching for disruption until it becomes arrears |
| M | Resilience | Nothing is disclosed, so nothing is flagged |
| Q | Capability | The product design creates the vulnerability, not the person |
| Dr. No | Health | A disclosure made once evaporates instead of persisting |

Lord Overdraft's stake in all four: it's *his* name on the attestation that says Old Street Mutual caught them.

---

*Old Street Mutual, Lord Overdraft, and all personas above are fictional constructs created for this portfolio piece. All regulatory references (FCA Consumer Duty, FG21/1, GDPR/ICO) describe real UK frameworks; the company and characters applying them do not exist.*
