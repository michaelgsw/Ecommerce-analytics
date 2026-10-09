"""Generate aggregate-only customer findings and reproducible validation evidence."""

import json

from .run_analysis import ROOT, decimal_ratio


def finding(lines, title, metric, comparison, interpretation, limitation):
    """Keep the metric and its interpretation/limits together for review."""
    lines.extend([f"## {title}", "", f"- Exact metric: {metric}",
                  f"- Comparison: {comparison}", f"- Interpretation: {interpretation}",
                  f"- Limitation: {limitation}", ""])


def percent(numerator, denominator):
    return decimal_ratio(100 * numerator, denominator) + "%"


def write_customer_reports(evidence):
    results, summary = evidence["results"], evidence["summary"]
    lines = ["# Customer Analysis Validation", "",
             f"Run (UTC): {evidence['validated_at_utc']}.", "",
             f"**PASS: {len(evidence['checks'])} independent checks and four exact CSV readbacks; zero failures.**", "",
             "## Scope and methods", "",
             "All customer behavior uses delivered orders, with customer_id only bridging orders to "
             "customer_unique_id. The reusable customer_level CTE is the analytical table: one row per "
             "persistent customer. It remains read-only and is not materialized into the database. "
             "It includes first/last purchase dates, order/item counts, exact item sales/freight, exact "
             "AOV numerator/denominator and rational text, first-to-last calendar days, repeat flag, "
             "consistent state, observation date, recency, missing-item/state flags, and cohort month.", "",
             "Items are aggregated per order before customer joins; customer-month activity is "
             "deduplicated before cohort joins; category activity is aggregated per order/category "
             "before customer joins. Repeat transitions have exactly one row per consecutive order "
             "pair. Independent expected results are rebuilt from base tables using Python integer "
             "sums, sets, counters, datetime parsing and sorting, without analytical SQL/CTEs. "
             "Every customer field and classification, every summary metric, all 100 Pareto cutoffs, "
             "and every cohort cell are checked, including types and NULL positions.", "",
             "All monetary sums remain INTEGER hundredths of unspecified source units. Ratios retain "
             "integer numerator/denominator pairs; display uses six-place Decimal half-up text. "
             "The wide retention matrix preserves exact counts and its original cohort denominator "
             "in new_customers. No binary floating-point amount is accepted. Timestamp ordering uses "
             "the unmodified naive source timestamps, with order_id as a deterministic tie breaker. "
             "Date intervals count calendar days; no source timezone is assigned.", "",
             "## Reconciliation", "",
             f"- Customer rows: {summary['customers']:,}, each with a distinct customer_unique_id.",
             f"- Completed orders: {summary['orders']:,}; sum of customer, segment and cohort order counts.",
             f"- Item sales: {summary['item_sales_hundredths']:,} hundredths; exact customer, segment, cohort and category sums.",
             f"- Repeat customers: {summary['repeat_customers']:,}; equals the prior validated result.",
             f"- Consecutive repeat pairs: {summary['orders'] - summary['customers']:,}; orders minus customers.",
             f"- Unassigned customer states: {summary['customer_state_unassigned']:,}; inconsistent/missing states stay NULL.", "",
             "## Retention denominators and missing observation", "",
             "Every M1/M2/M3/later-month rate divides distinct customers returning in that specific "
             "calendar month by the original first-observed-completed-purchase cohort size. This is "
             "monthly return activity, not survival, cumulative repeat, or order count. Customers may "
             "return in several months; these numerators cannot be added as distinct customers. "
             "Month 0 is 100% cohort membership, not repeat retention. Observed repeat rate uses "
             "customers with at least two completed orders anywhere in the available history / "
             "original cohort size, including same-month and terminal-month orders.", "",
             "For primary retention rates, target months after August 2018 are future_unobserved, "
             "August 2018 is terminal_partial, and November 2016 is calendar_gap. Their returning "
             "counts/rates are NULL (blank CSV fields). Actual observed terminal-month activity is "
             "retained separately in observed_customers. The gap's observed zero only describes "
             "the extract; it is not a zero-retention estimate. Interior observed months permit "
             "descriptive rates but are not certified complete. M4+ counts distinct customers over "
             "eligible interior offsets >=4, excludes terminal partial activity, and is NULL when "
             "none of these months is available. Cohort repeat totals have a broader observation "
             "basis than these conservative retention rates. First/terminal cohorts and insufficient "
             "first-three-month coverage are flagged.", "",
             "## Checks", ""]
    lines.extend(f"- PASS: {check['name']}." for check in evidence["checks"])
    lines.extend(["- PASS: four saved CSVs reread with identical headers, rows, fields, blanks and Decimal displays.",
                  f"- PASS: all {len(evidence['protected_hashes'])} protected database/schema/raw/processed/prior-export files retain identical SHA-256 hashes.",
                  "- PASS: database hash matches independent database evidence; five prior export hashes match prior metric evidence.", "",
                  "## Outputs and reproduction", ""])
    lines.extend(f"- data/analytics/{name}.csv: {count:,} aggregate rows." for name, count in evidence["export_rows"].items())
    lines.extend(["", "No customer/order identifiers appear in exports or the aggregate JSON evidence. "
                  "JSON retains every aggregate result (including full concentration, interval and "
                  "category distributions), query/input/export hashes and check outcomes.", "",
                  "```powershell", ".\\.venv\\Scripts\\python.exe -m src.analysis.run_customer_analysis",
                  ".\\.venv\\Scripts\\python.exe -m src.analysis.run_customer_analysis --validate-only", "```", "",
                  "Each numbered SQL file contains complete, separately marked SELECT statements. "
                  "Shared CTE copies are drift-checked. CSVs are staged/read back and replaced individually; "
                  "CSV/report publication is not a single filesystem transaction. Run one instance at "
                  "a time and revalidate after interrupted publication.", "",
                  "**These results are reconciled and usable for descriptive customer analysis under "
                  "the documented definitions.** Boundary coverage, finite customer history, tied "
                  "timestamps, unknown categories, state ambiguity and monetary semantics remain "
                  "interpretation limits. See customer_analysis_methodology.md and the findings report.", ""])
    (ROOT / "reports/customer_analysis_validation.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports/customer_analysis_validation.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_findings(evidence)


def write_findings(evidence):
    results, summary = evidence["results"], evidence["summary"]
    groups = {row["frequency_group"]: row for row in results["purchase_group_comparison"]}
    repeat, one_time = groups["Repeat"], groups["One-time"]
    timing = {row["metric"]: row for row in results["repeat_purchase_summary"]}
    statistics = {row["statistic"]: row for row in results["value_statistics"]}
    lines = ["# Customer Analysis Findings", "",
             f"Validated (UTC): {evidence['validated_at_utc']}. Eligible population: "
             f"{summary['customers']:,} persistent customers, {summary['orders']:,} delivered orders, "
             f"{summary['item_sales_hundredths']:,} item-sales hundredths.", "",
             "Money is expressed in exact hundredths without a currency assertion. Displayed ratios "
             "are Decimal values rounded to six places; their exact integer components remain in "
             "the CSV/JSON evidence. All findings describe the available historical extract.", ""]
    finding(lines, "Purchase frequency and customer value",
            f"{repeat['customers']:,}/{summary['customers']:,} customers repeat "
            f"({percent(repeat['customers'], summary['customers'])}); repeat sales are "
            f"{repeat['item_sales_hundredths']:,}/{summary['item_sales_hundredths']:,} hundredths "
            f"({repeat['sales_share_percent']}%).",
            f"One-time customers: {one_time['customers']:,}; mean customer sales "
            f"{one_time['average_customer_sales_hundredths']} hundredths versus "
            f"{repeat['average_customer_sales_hundredths']} for repeat customers. "
            f"AOV: {one_time['average_order_value_hundredths']} versus "
            f"{repeat['average_order_value_hundredths']} hundredths. "
            "Frequency distribution: " + "; ".join(f"{r['completed_order_count']} order(s): {r['customers']:,} customers" for r in results["frequency_distribution"]) + ".",
            "The population has very little observed frequency variation. Repeat customers contribute "
            "more total observed sales per customer; this includes their additional orders.",
            "These are observed purchases, not lifetime behavior or causal effects of repeating. "
            "Later acquisitions have less follow-up; same-day orders can include split/batched transactions.")
    pareto = {row["target_customer_percent"]: row for row in results["pareto_concentration"]}
    inverse = results["customers_for_80_percent_sales"][0]
    finding(lines, "Actual customer sales concentration",
            "; ".join(f"Top {p}% ({pareto[p]['customers_selected']:,} customers): "
                      f"{pareto[p]['item_sales_hundredths']:,} hundredths, "
                      f"{pareto[p]['cumulative_sales_percent']}% of sales" for p in (1, 5, 10, 20)) + ".",
            f"Reaching at least 80% requires {inverse['customers_selected']:,} customers "
            f"({inverse['customer_share_percent']}%), contributing {inverse['item_sales_hundredths']:,} "
            f"hundredths ({inverse['sales_share_percent']}%). Top 20% falls below 80%.",
            "Sales are concentrated, but the observed data does not follow an 80/20 split. "
            "All 100 cumulative percentile points are retained in the JSON evidence.",
            "Top groups use ceil(N*p/100); exact-N boundary ties are ordered deterministically by "
            "persistent ID, without exporting IDs. These groups measure observed item sales, "
            "not profit, net revenue, payment receipts or lifetime value.")
    finding(lines, "Statistically supported descriptive segments",
            f"Q1={statistics['Q1']['value_numerator']:,}, median={statistics['median']['value_numerator']:,}, "
            f"Q3={statistics['Q3']['value_numerator']:,}, P90={statistics['P90']['value_numerator']:,}, "
            f"P95={statistics['P95']['value_numerator']:,}, P99={statistics['P99']['value_numerator']:,} hundredths. "
            f"High value means item sales strictly above Q3+1.5*(Q3-Q1) = "
            f"{statistics['Tukey_upper_fence']['value']} hundredths.",
            "; ".join(f"{r['segment']}: {r['customers']:,} customers, {r['customer_share_percent']}% of customers, "
                      f"{r['item_sales_hundredths']:,} hundredths, {r['sales_share_percent']}% of sales" for r in results["customer_segments"]) + ".",
            "The four groups separate observed purchase multiplicity and the robust upper-value tail. "
            "The threshold was chosen after inspecting the skewed distribution. Ties at the threshold "
            "remain standard, and ties are never split to force equal segment sizes. This is a useful "
            "descriptive distinction for this extract.",
            "The Tukey rule identifies an upper tail; it does not establish natural clusters, "
            "future value, loyalty or lifetime value. Segment means are partly defined by the rule, "
            "not independent proof of predictive usefulness. Customer tenure and acquisition date differ.")
    finding(lines, "Historical recency and consistent state",
            f"Reference date: {summary['observation_date']}, the latest observed delivered-order purchase "
            f"date. Nearest-rank median recency: {statistics['recency_median']['value_numerator']} calendar days. "
            f"{summary['customer_state_unassigned']:,} customer states remain NULL.",
            "; ".join(f"{r['recency_group']}: {r['customers']:,} customers; recency range "
                      f"{r['min_recency_days']}–{r['max_recency_days']} days" for r in results["recency_summary"]) + ".",
            "Recent within observed period means recency <= the observed median; less recent means "
            "greater than it. State is assigned only when all completed-order-associated customer "
            "records have one consistent, nonblank source state.",
            "The reference date is an extract boundary, not a certified business cutoff or today's "
            "date. These labels do not describe currently active/churned customers. State is the "
            "customer-record location, not verified delivery geography; geolocation is not joined.")
    cohorts = results["customer_cohort_summary"]
    common = [row for row in cohorts if not row["flag_insufficient_three_month_coverage"]]
    denominator = sum(row["new_customers"] for row in common)
    trajectory = []
    for month in (1, 2, 3):
        n = sum(row[f"customers_returning_month_{month}"] for row in common)
        trajectory.append(f"M{month}: {n:,}/{denominator:,} = {percent(n, denominator)}")
    cells = results["cohort_retention_long"]
    coverage = {status: sum(row["coverage_status"] == status for row in cells)
                for status in sorted({row["coverage_status"] for row in cells})}
    finding(lines, "Cohort return activity with explicit observation limits",
            f"{len(cohorts)} cohorts reconcile to {summary['customers']:,} customers. "
            f"For the same {len(common)} cohorts with all M1–M3 interior observation, " + "; ".join(trajectory) + ".",
            f"{sum(r['flag_insufficient_three_month_coverage'] for r in cohorts)} cohorts lack full first-three-month "
            f"interior coverage. Matrix statuses across {len(cells)} cells: " + "; ".join(f"{k}={v}" for k, v in coverage.items()) + ". "
            f"{summary['same_month_repeat_customers']:,} customers repeat within their acquisition month; "
            "monthly return activity measures a different behavior than any observed repeat order.",
            "Later-month activity is low in the shared observed cohort population. Month-specific "
            "rates count returning customers against each original cohort size; they are not "
            "cumulative and need not decline monotonically.",
            "First acquisition is first observed, not proven first ever. The initial cohort, "
            "November 2016 gap and August 2018 terminal partial month limit interpretation. Future, "
            "gap and terminal-partial rates are blank, not zero. Older cohorts' overall repeat "
            "rates have longer follow-up. Interior months are descriptive and not certified complete. "
            "Small cohorts are unstable: September and December 2016 each contain one observed customer; "
            "December's 1/1 M1 rate is 100% and cannot represent typical customer behavior.")
    lines.extend(["Cohort-level comparisons (item sales and means include all observed delivered purchases; "
                  "M1/M2/M3 primary rates use the conservative coverage rule):", ""])
    for row in cohorts:
        rates = "; ".join(f"M{m}=" + (str(row[f'month_{m}_retention_percent']) + "%" if row[f'month_{m}_retention_percent'] is not None else "NULL") + f" ({row[f'month_{m}_coverage']})" for m in (1, 2, 3))
        later = row['customers_returning_month_4_plus']
        lines.append(f"- {row['cohort_month']}: new={row['new_customers']:,}, repeat={row['repeat_customers']:,} "
                     f"({row['observed_repeat_rate_percent']}%), sales={row['item_sales_hundredths']:,} hundredths, "
                     f"mean={row['average_customer_sales_hundredths']} hundredths; {rates}; "
                     f"distinct M4+ returns={later if later is not None else 'NULL'}; "
                     f"interior future months={row['available_interior_future_months']}.")
    lines.append("")
    finding(lines, "Conditional repeat-purchase timing",
            f"Median first-to-second interval among {summary['repeat_customers']:,} observed repeat "
            f"customers: {timing['median_days_to_second_purchase']['value']} calendar days. "
            + "; ".join(f"Within {days} days: {timing[f'within_{days}_days']['count']:,}/"
                        f"{summary['repeat_customers']:,} ({timing[f'within_{days}_days']['value']}%)" for days in (30, 60, 90, 180)) + ".",
            f"Same-day seconds: {timing['same_day_second_purchase']['count']:,} "
            f"({timing['same_day_second_purchase']['value']}%); identical first/second timestamps: "
            f"{timing['first_second_timestamp_ties']['count']:,}. All consecutive intervals: "
            f"{timing['all_consecutive_repeat_intervals']['count']:,}, versus one first-to-second "
            f"interval per repeat customer ({summary['repeat_customers']:,}).",
            "A substantial share of observed seconds occurs quickly, and same-day purchases materially "
            "affect the interval distribution. Detailed mutually exclusive day bins are retained below.",
            "Denominator is only observed repeat customers. These percentages are not probabilities "
            "that any customer will repeat within those windows, and do not adjust for censoring. "
            "Same-day/tied timestamps cannot establish separate shopping intent. Deterministic ID "
            "ordering resolves ties computationally, not their true purchase sequence.")
    lines.extend(["Interval distributions (calendar days; each interval belongs to one bin):", ""])
    for row in results["repeat_interval_distribution"]:
        lines.append(f"- {row['scope']} / {row['interval_bin']}: {row['intervals']:,} intervals, "
                     f"observed range {row['min_days']}–{row['max_days']} days.")
    lines.append("")
    transitions = results["category_transitions"]
    finding(lines, "Category continuity and movement",
            "; ".join(f"{r['scope']} / {r['behavior']}: {r['order_transitions']:,} transitions "
                      f"({r['transition_share_percent']}%)" for r in transitions if r['scope'] == 'first_to_second') + ".",
            "; ".join(f"All consecutive / {r['behavior']}: {r['order_transitions']:,} transitions "
                      f"({r['transition_share_percent']}%)" for r in transitions if r['scope'] == 'all_consecutive') + ".",
            "Same known category set means identical sets across the two orders; disjoint sets mean "
            "no common category; overlapping change means some shared categories with a changed set. "
            "Category pair counts cover the interval population exactly without item join multiplication.",
            "Any missing category or order with no items makes the transition unknown; none is forced "
            "into same/different. Orders may have several categories. Distinct customers can appear "
            "in several transition classes and are not additive. Timestamp ties make sequence "
            "interpretation ambiguous; category movement does not prove intent or loyalty.")
    categories = results["category_customer_behavior"]
    top = [row for row in categories if row['sales_rank'] <= 5]
    finding(lines, "Top observed categories by customer purchase group",
            "; ".join(f"{r['frequency_group']} #{r['sales_rank']} {r['product_category_name'] or 'source NULL'}: "
                      f"{r['item_sales_hundredths']:,} hundredths, {r['group_sales_share_percent']}% of "
                      f"group sales, {r['customers']:,} customers" for r in top) + ".",
            f"Rankings compare one-time versus repeat customers within their own group sales "
            f"denominator; all {len(categories)} group/category rows remain in JSON evidence, "
            "including missing and untranslated labels.",
            "The rankings show merchandise contribution associated with each observed customer "
            "group, after reducing item rows to order/category.",
            "Category customers/orders can overlap across categories and cannot be summed. Group "
            "membership uses full observed history, so these rankings do not isolate the category "
            "of the return purchase or establish that a category causes repeat behavior.")
    lines.extend(["## Limits relevant to later dashboard design", "",
                  "- Keep historical recency labels, original cohort sizes/denominators and all coverage flags visible. "
                  "Tiny cohorts can produce extreme rates. Blank future/partial/gap rates must remain distinguishable "
                  "from measured interior zeros; M0 is membership.",
                  "- Preserve the delivered-only definition, persistent-customer grain and calendar-day convention. "
                  "Cohort repeat and month-specific return activity have different observation bases.",
                  "- Show conditional timing denominators and same-day/timestamp-tie counts; avoid labeling these shares "
                  "as uncensored repeat likelihood. Missing categories and ambiguous states remain unknown.",
                  "- Keep monetary scale explicit; observed sales exclude freight and unsupported refund/profit adjustments. "
                  "Means and segment differences do not demonstrate predictive value or natural customer classes.", "",
                  "These are factual findings and presentation limits. A final dashboard and strategic recommendations "
                  "remain outside this stage.", ""])
    (ROOT / "reports/customer_analysis_findings.md").write_text("\n".join(lines), encoding="utf-8")
