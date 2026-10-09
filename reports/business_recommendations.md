# Business recommendations: hypotheses to test

These proposals are grounded in the validated historical findings. They are
**testable hypotheses**, not demonstrated causal effects or revenue forecasts.
No campaigns, customer contact, targeting exports or operational changes have
been performed. Historical aggregates do not identify a current reachable audience;
prospective testing requires current customer history and appropriate campaign
eligibility. [Supporting findings](final_business_findings.md) retain exact metrics,
comparisons and limitations.

The future experiment KPIs below are explicitly **new proposed monitoring
definitions**, not replacements for current dashboard KPIs. Their data is not
available in this handoff and no results are claimed. Keep equal follow-up windows,
concurrent randomized controls where practical and complete eligibility/assignment
counts. Report uncertainty and adverse outcomes alongside any observed lift.

## 1. Test retention outreach for a current high-value one-time population

- Observed evidence: 7,095 high-value one-time customers represent 7.599777% of
  customers but 34.563959% of historical item sales; only 3.000278% of all customers
  have an observed second completed order.
- Proposed business action: first verify the rule on current data, then randomly
  assign currently eligible one-time upper-value customers to a relevant follow-up
  offer or a concurrent holdout. Define value eligibility before assignment;
  do not let later purchases change the original experimental group. Use the
  historical Tukey rule as a candidate segmentation rule to validate, not a
  universal monetary cutoff or proven prediction.
- Expected business objective: test whether incremental completed repeat activity
  and recorded customer contribution can improve for this descriptive population.
- KPI to monitor: proposed 90-day second-completed-order incidence = assigned
  customers with a second completed order within 90 days / all eligible assigned
  customers with a completed 90-day follow-up. Compare treatment and holdout
  percentage points; report 90-day observed item sales per assigned customer and
  campaign/offer cost. Cost-adjusted contribution requires additional reliable costs.
- Limitation / what needs testing: observed high value does not imply future
  responsiveness. Revalidate threshold stability, contactable population, tenure
  and full follow-up. Historical conditional repeat shares cannot supply an
  expected treatment lift, budget return or sample-size assumption without new data.

## 2. Test post-purchase timing rather than assuming an optimal campaign day

- Observed evidence: among observed repeat customers the median first-to-second
  interval is 29 days; 50.553374% repeat within 30 days. Same-day seconds are
  29.596573%, including 253 exact first/second timestamp ties.
- Proposed business action: compare a small number of predeclared follow-up timing
  arms (for example day 14 and day 28) with a no-additional-contact control among
  newly eligible current purchasers. Log assignment, message exposure and actual
  completed orders. Review same-day/batched orders separately without rewriting
  the current historical delivered-order definition.
- Expected business objective: learn whether follow-up timing changes incremental
  completed second-purchase incidence and whether any benefit exceeds campaign cost.
- KPI to monitor: proposed 60/90-day second-completed-order incidence over all
  assigned customers with equal follow-up, treatment-control difference and
  observed item sales per assigned customer. Track unsubscribe/complaint rates
  and campaign cost as guardrails.
- Limitation / what needs testing: the 29-day median is conditional on having
  repeated and is not a causal optimum. Censoring, split transactions and delivery
  cycles may alter interpretation. The existing 30/60/90/180 shares must not be
  reused as the experiment's all-customer incidence rates.

## 3. Compare cross-category and same-category recommendations experimentally

- Observed evidence: first-to-second category sets have no overlap in 51.231703%
  of pairs, identical sets in 45.019636%, changed overlapping sets in 1.285255%,
  and unknown categories in 2.463406%.
- Proposed business action: using a current catalog and usable customer-category
  history, compare relevant cross-category recommendations, same-category
  recommendations and a control. Randomize comparable recommendation opportunities
  or customers consistently; define the exposure and attribution window before launch.
- Expected business objective: test whether either recommendation approach produces
  additional completed orders and observed sales beyond the control experience.
- KPI to monitor: proposed attributed completed-order conversion per assigned
  opportunity/customer with a fixed follow-up window; completed item sales per
  assigned unit; share of known-category orders that include a different category.
  Report unknown-category coverage separately. Choose one randomization grain and
  use it consistently in all denominators.
- Limitation / what needs testing: aggregate transitions do not provide item-pair
  affinity, available stock, current preferences or causal recommendation impact.
  Known-category eligibility can select a different population; report exclusions.
  Timestamp ties and multi-category sets prevent inferring a true directional journey.

## 4. Separate acquisition reporting from comparable follow-up reporting

- Observed evidence: 90,557 customers have one observed completed order. Across
  the same 17 covered cohorts, M1/M2/M3 activity rates are 0.482381% / 0.349762% /
  0.262322%; six cohorts lack common first-three-month coverage.
- Proposed business action: use the dashboard's separate acquisition size,
  common-coverage monthly returns and full-history conditional timing views in
  reviews. In a future current-data refresh, retain equal observation windows,
  cohort sizes and outcome-maturity checks before comparing acquisition periods.
  Test whether this reporting structure reduces decisions based on incomparable rates.
- Expected business objective: improve the comparability of acquisition and
  follow-up evaluation and make experiment populations auditable.
- KPI to monitor: existing first-observed completed-purchase cohort sizes and
  original-size monthly return rates, with eligible-cohort/customer counts and
  coverage status. Monitor the percentage of cohorts with completed comparable
  follow-up and whether decisions use the documented denominator.
- Limitation / what needs testing: better reporting alone does not prove higher
  sales. Interior history is not certified complete, small cohorts are unstable,
  and overall historical repeat rate is not directly comparable across customer tenure.

## Evidence required before interpreting an intervention

Add current assignment/exposure logs, the operational eligibility definition,
complete observed purchase outcomes over the chosen windows, and costs/refunds
if evaluating profitability. Define a minimum detectable effect and sample size
from an appropriate current baseline; the conditional historical timing shares
are insufficient. Review treatment-control uncertainty before scaling. Preserve
the current historical KPI definitions and keep future experiment metrics in a
separate documented analytical extension.
