-- One governed dataset, seven thin lenses (ADR-04). POC choices are marked.

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_overdraft` AS
WITH scope AS (SELECT 5 AS members_in_scope)  -- POC: five synthetic members
SELECT DATE(c.created_at) AS day,
       COUNT(*) AS cases,
       COUNT(DISTINCT c.member_id) AS members_assessed,
       ROUND(100 * COUNT(DISTINCT c.member_id) / ANY_VALUE(s.members_in_scope), 1) AS coverage_pct,
       COUNTIF(c.accepted_n > 0) AS flagged_cases,
       COUNTIF(c.accepted_n > 0 AND f.case_id IS NOT NULL) AS flagged_drillable,
       ROUND(100 * SAFE_DIVIDE(COUNTIF(c.accepted_n > 0 AND f.case_id IS NOT NULL),
                               COUNTIF(c.accepted_n > 0)), 1) AS drillthrough_pct
FROM `lumen-poc-srao26.sludge_gov.cases` c
LEFT JOIN (SELECT DISTINCT case_id FROM `lumen-poc-srao26.sludge_gov.findings`) f ON f.case_id = c.case_id
CROSS JOIN scope s
GROUP BY day;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_vetter` AS
SELECT c.created_at, c.case_id, c.member_id, c.status, c.review_state, c.outcome,
       f.driver, f.grounded, f.confidence, f.rationale, f.evidence,
       f.decision, c.reviewer, c.review_note
FROM `lumen-poc-srao26.sludge_gov.cases` c
LEFT JOIN `lumen-poc-srao26.sludge_gov.findings` f ON f.case_id = c.case_id;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_escalade` AS
SELECT DATE(created_at) AS day,
       COUNT(*) AS findings_total,
       COUNTIF(grounded) AS grounded,
       ROUND(100 * SAFE_DIVIDE(COUNTIF(grounded), COUNT(*)), 1) AS grounding_pass_pct,
       SAFE_DIVIDE(COUNTIF(grounded), COUNT(*)) >= 0.95 AS meets_target
FROM `lumen-poc-srao26.sludge_gov.findings`
GROUP BY day;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_paisawala` AS
SELECT DATE(created_at) AS day,
       COUNT(*) AS cases,
       COUNTIF(failed_attempts > 0) AS cases_with_retries,
       SUM(failed_attempts) AS failed_attempts,
       COUNTIF(status = 'queued_error') AS queued_errors,
       ROUND(100 * SAFE_DIVIDE(COUNTIF(status = 'queued_error'), COUNT(*)), 1) AS queued_error_pct
FROM `lumen-poc-srao26.sludge_gov.cases`
GROUP BY day;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_redact` AS
SELECT c.created_at, c.case_id, c.member_id,
       IFNULL(c.lawful_basis, 'not recorded') AS lawful_basis,
       c.retain_until,
       DATE_DIFF(DATE(c.retain_until), CURRENT_DATE(), DAY) AS days_remaining,
       CASE WHEN c.retain_until IS NULL THEN 'not recorded'
            WHEN c.retain_until < CURRENT_TIMESTAMP() THEN 'expired'
            ELSE 'active' END AS retention_state,
       IFNULL(a.access_entries, 0) AS access_entries,  -- one entry per case per minute
       a.last_viewed
FROM `lumen-poc-srao26.sludge_gov.cases` c
LEFT JOIN (SELECT case_id, COUNT(*) AS access_entries, MAX(viewed_at) AS last_viewed
           FROM `lumen-poc-srao26.sludge_gov.access_log` GROUP BY case_id) a ON a.case_id = c.case_id;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_ledger` AS
WITH priced AS (
  SELECT DATE(created_at) AS day, member_id, status, tokens_in, tokens_out,
         -- Verified rate for gemini-3.5-flash-lite: USD per million tokens. Other models are unpriced.
         CASE model WHEN 'gemini-3.5-flash-lite' THEN 0.30 END AS usd_in,
         CASE model WHEN 'gemini-3.5-flash-lite' THEN 2.50 END AS usd_out
  FROM `lumen-poc-srao26.sludge_gov.cases`
), daily AS (
  SELECT day, COUNT(*) AS cases, COUNT(DISTINCT member_id) AS members_assessed,
         SUM(IFNULL(tokens_in, 0)) AS tokens_in, SUM(IFNULL(tokens_out, 0)) AS tokens_out,
         SUM(IFNULL(tokens_in, 0) * usd_in + IFNULL(tokens_out, 0) * usd_out) / 1e6 AS cost_usd
  FROM priced GROUP BY day
)
SELECT day, cases, members_assessed, tokens_in, tokens_out,
       ROUND(cost_usd, 6) AS cost_usd,
       ROUND(cost_usd / cases, 6) AS cost_per_case_usd
FROM daily;

CREATE OR REPLACE VIEW `lumen-poc-srao26.sludge_gov.lens_trustwell` AS
WITH d AS (
  SELECT DATE(created_at) AS day,
         COUNTIF(decision IS NOT NULL) AS decided,
         COUNTIF(decision = 'dismiss') AS overridden,
         AVG(confidence) AS avg_confidence
  FROM `lumen-poc-srao26.sludge_gov.findings`
  WHERE grounded
  GROUP BY day
), w AS (
  SELECT *, LAG(avg_confidence) OVER (ORDER BY day) AS prev_avg FROM d
)
SELECT day, decided, overridden,
       ROUND(SAFE_DIVIDE(overridden, decided), 3) AS override_rate,
       CASE WHEN decided < 10 THEN 'insufficient_data'
            WHEN overridden = 0 THEN 'rubber_stamp_risk'
            ELSE 'ok' END AS override_signal,
       ROUND(avg_confidence, 3) AS avg_confidence,
       ROUND(SAFE_DIVIDE(avg_confidence - prev_avg, prev_avg), 3) AS confidence_drift,
       -- POC: the design doc leaves X unset; 10% day-over-day is my placeholder.
       ABS(SAFE_DIVIDE(avg_confidence - prev_avg, prev_avg)) > 0.10 AS drift_flag
FROM w;
