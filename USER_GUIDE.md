# SLUDGE user guide

SLUDGE is a demonstration tool for the fictional building society Old Street Mutual. It reads synthetic member conversations, flags possible Consumer Duty outcome failures, and asks a human reviewer to confirm or dismiss each finding. All data is synthetic, and no real members or accounts are involved.

This guide shows you how to review findings and read the Governance page.

## Before you begin

- Open the app at the address in the project README, or use the **Launch app** button in the design doc.
- You don't need to sign in.
- The app accepts five synthetic members: M-1001 to M-1005.

## Review a finding

The reviewer page lists the cases that need a decision. Each member appears at most once, and only if their newest case is still pending.

To review a case:

1. Open a case from the queue. The page shows each finding with the evidence the model cited.
2. Read the finding and its citations. The automated checks confirm that citations exist. They don't confirm that the citation supports the finding, so you make that judgment.
3. Choose **Confirm** if the finding is right, or **Dismiss** if it is wrong.
4. Optionally add a note that explains your decision.
5. Submit the decision. The case moves out of the queue, and the Governance page updates within a few seconds.

Opening a case writes an entry to the access log. If the app can't write the entry, it doesn't show the case.

## Run a new assessment

You can run an assessment for any of the five members.

1. Choose a member.
2. Start the assessment and wait for the result. It usually takes a few seconds.
3. If the system finds nothing, the member has no case in the queue.
4. If it finds something, a new case appears in the queue.

The app runs at most 20 assessments a day. After that, it returns a "too many requests" message until the next day.

## Read the Governance page

The Governance page has seven sections, one for each role that cares about the data. They all read from the same governed dataset.

| Section | What it answers |
| --- | --- |
| Overdraft | How much of the monitored population the system covers. |
| Vetter | Which findings are pending, and which are decided. |
| Escalade | Which cases were recommended for escalation. |
| Paisawala | Whether the pipeline is healthy. |
| Redact | Lawful basis, retention dates and who opened each case. |
| Ledger | What the system costs to run. |
| Trustwell | How often reviewers override the model, and how well its findings are grounded. |

Each section shows a short question, a status line and a table.

### Data freshness

The Governance page caches each section for up to five minutes. After you confirm or dismiss a finding, the page refreshes its cache. If the table still looks old, wait a minute and reload.

### Override rate

The override rate is the share of decided findings that reviewers dismissed. The page shows one of three signals:

- **Insufficient data**: fewer than 10 findings are decided, so no conclusion is possible.
- **OK**: the rate is within the expected range.
- **Rubber-stamp risk**: reviewers rarely dismiss anything, which can mean they aren't checking each finding.

## Troubleshooting

| Symptom | Cause | What to do |
| --- | --- | --- |
| A case is missing from the queue. | A newer case for the same member exists, or the case is already decided. | Check the Vetter section on the Governance page. |
| The assessment returns "too many requests". | The daily limit of 20 is used up. | Try again tomorrow. |
| A case doesn't open. | The access log could not be written. | Reload and try again. |
| A table shows old data. | The five-minute cache has not expired. | Wait and reload. |
