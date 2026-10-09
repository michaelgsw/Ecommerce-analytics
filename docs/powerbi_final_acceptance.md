# Final Power BI dashboard acceptance

Date: 2026-10-07 (America/New_York). Report: powerbi/Ecommerce.pbip.

**Status: ACCEPTED - all four pages passed user-confirmed manual Desktop acceptance and the final dashboard QA pass.** Page 4 is now accepted. No presentation correction was necessary during final QA.

## Evidence and scope

Authoritative references: [dashboard specification](powerbi_dashboard_spec.md), [PBIR authoring research](pbir_authoring_research.md), accepted page implementations and the user's final manual acceptance confirmation. Later explicit page instructions and accepted analytical definitions take precedence over earlier planning text.

Final QA included a fresh powerbi-report-author Desktop --all-pages --scale 2 screenshot capture and review of all four pages; saved PBIR formatting, text, filters and every directed interaction; read-only EVALUATE queries against the running Desktop semantic model; and SHA256 preservation checks. The existing accepted Desktop session was inspected without reload or save. No report content was edited. Screenshots were temporary validation artifacts and removed after review.

Live slicer behavior is accepted on the user's reported manual Desktop testing. The agent independently checked saved interaction definitions and filtered measure results; it did not perform a new round of UI clicks. All local slicers appeared at All in the final screenshots.

## Page-by-page results

1. **Executive Overview - PASS.** Six aligned KPI cards retain full counts/source-unit amounts and two-decimal percentage displays. Monthly columns remain chronological, with November 2016 and September/October 2018 blank in the chart. Top 10 categories remain sales-descending and full-history; operational status remains all observed orders. Monthly coverage detail has intentional vertical scrolling for 26 months, all six columns visible, no inappropriate total and an explicitly labeled raw hundredths audit column. Historical coverage, the 99,441 all-order denominator, freight exclusion and unconfirmed currency are disclosed.
2. **Customer Value & Segmentation - PASS.** Count, sales, customer mean/AOV, concentration, top-group contribution, segment table and high-value highlight visuals render correctly. Sales-share labels show percentages without compact units, and amount labels retain source units. The segment table fits its seven columns without scrolling. Concentration/high-value titles preserve full-history scope; segment definitions, historical recency and non-predictive limitations remain visible.
3. **Retention & Cohorts - PASS.** M0-M23 are visible across the matrix without horizontal scrolling. Later cohort rows use intentional vertical scrolling. Dark text and distinct M0/FU/CG/TP/zero/positive backgrounds render correctly. M1/M2/M3 cards show 0.482% / 0.350% / 0.262%; the coverage note shows 17 cohorts / 68,618 customers. Median 29.0 days, four cumulative timing shares and seven interval counts remain correct. Cohort and repeat-timing populations are visibly separated; the legend and follow-up limitations are present. Bottom-row evidence and slicer isolation were manually accepted by the user.
4. **Product & Category Performance - PASS.** All six category-table columns render within the container, sorted by sales descending, with readable source-unit sales data bars and no grand total. The complete 74-group population, one missing-source group and two untranslated groups remain preserved. Category mix uses separate One-time/Repeat percentage bars. Continuity remains fixed to the 2,801 first-to-second pairs. Vertical scrolling in the complete category table/mix is intentional. Category-level scope, fixed denominators, overlapping memberships, unknown categories and no causal-affinity implication remain disclosed.

## Cross-page presentation audit

- Shared theme, Segoe UI text, semibold page headings, business visual titles, white rounded containers and consistent margins/gutters are retained. Density varies appropriately by page. Comparative series colors and neutral operational status are intentional.
- No visible broken visual, overlap, unintended clipping, missing business title, mojibake, non-ASCII dash or technical/debug subtitle was found. Saved page/visual JSON has no non-ASCII strings, enabled automatic subtitles or out-of-canvas visual bounds.
- KPI counts use full values and zero decimal places; source-unit sales/AOV show two decimal places with no currency symbol. Percentage labels use None display units. General percentages use two decimal places; common cohort cards intentionally use three. Median uses the accepted one-decimal style. Compact K/M chart axes and Page 1 category amount labels are intentional and readable; source-unit meaning remains explicit.
- No unnecessary horizontal scrollbar was found. The coverage table, cohort matrix and complete category lists intentionally scroll vertically; removing those scrollbars would hide required detail or crowd the page.
- All pages disclose historical scope and limited filter reach. Monetary visuals retain source-unit definitions; freight exclusion is explicit in report disclosures. Page-specific notes explain weighted denominators, cohort observation states and repeat/category population limits rather than applying incompatible populations across pages.

## Tested slicer interactions and saved-definition audit

Manual Desktop acceptance was confirmed by the user for all four pages. The saved report independently contains all 374 directed pairs across the data visuals: 20 intended DataFilter pairs and 354 NoFilter pairs, with no omitted/duplicate pair or unauthorized chart-to-chart filtering. No slicer sync configuration was found.

- **Page 1 Purchase month:** filters only monthly sales and monthly coverage; KPI cards, categories and status stay fixed. Local Product category filters only fixed-rank Top 10 categories; lower-ranked selections may intentionally leave that chart empty.
- **Page 2 Customer segment / Customer type:** each filters customer-type count/sales, mean-sales/AOV comparison and the segment table. Concentration, top customer contributions, inverse concentration cards and high-value one-time highlight remain full-history.
- **Page 3 Acquisition cohort:** filters cohort size, M1/M2/M3, selected common-coverage note and matrix. Median, cumulative windows and interval distribution stay unchanged. The user's explicit earlier test confirmed 2018-08/M0 = M0, 2018-08/M1 = FU, unavailable common M1-M3 population and unchanged timing values/counts.
- **Page 4 Product category:** filters overall category table and category mix, not continuity. Customer type exposes only One-time/Repeat and filters mix only. Manual acceptance closes the earlier pending interaction checks. Read-only selected-category context independently confirms health_beauty / stable source label beleza_saude retains 9.326717% overall share, with mix shares 9.434563% / 7.477024%, rather than resetting to 100%.

No chart-to-chart filtering is enabled. Slicers are local and are not synced across disconnected tables/pages.

## Accepted KPI baselines - unchanged

Read-only live measure queries reproduce the accepted baselines below. Percentages are percentage values, not underlying 0-to-1 fractions; six-decimal values are rounded for audit. AOV retains its original unrounded ratio (137.0415857501192) and displays 137.04.

**Executive Overview**

- Completed orders: 96,478.
- Unique completed customers: 93,358.
- Observed item sales: 13,221,498.11 source units.
- AOV: 137.04 source units.
- Observed repeat customer rate: 3.000278% (card 3.00%).
- Delivered order rate: 97.020344% (card 97.02%).

**Customer Value & Segmentation**

- One-time customers: 90,557.
- Repeat customers: 2,801.
- High-value one-time customers: 7,095.
- High-value one-time sales share: 34.563959% (card 34.56%).

**Retention & Cohorts**

- M1: 0.482381%; M2: 0.349762%; M3: 0.262322%.
- Common eligible population: 17 cohorts / 68,618 original customers.
- Median second purchase: 29 days (card 29.0).
- Within 30 / 60 / 90 / 180 days: 50.553374% / 61.121028% / 68.118529% / 82.863263%.
- First-to-second interval counts: 829 / 587 / 296 / 196 / 413 / 398 / 82.

**Product & Category Performance**

- Transition counts, in exported order: 1,261 / 36 / 1,435 / 69; total 2,801.
- health_beauty / beleza_saude overall share under category filtering: 9.326717% (table 9.33%).
- Overall category groups: 74, including the missing-source group and both untranslated labels.

## Blank-versus-zero checks

Read-only measures confirm 2016-09/M1 is numeric zero with text 0.00% and background #F3FAF5; 2016-09/M2 = CG with a blank numeric rate; 2018-06/M2 = TP with a blank numeric rate; 2018-08/M1 = FU with a blank numeric rate; 2018-08/M0 = M0 membership with a blank numeric return rate. Their unavailable/membership colors are #FFF2CC / #EDE4F7 / #E5E7EB / #DCE6F1 respectively. Selecting 2018-08 yields BLANK M1/M2/M3 and the no-common-coverage note. Monthly chart values for 2016-11 and 2018-09/10 remain BLANK even though raw observed totals are zero. No unavailable state was converted to a measured zero.

## Validation and known limitations

Command: powerbi-report-author validate powerbi/Ecommerce.Report. Final result: **2 known pre-existing errors, 1 existing warning, no new findings.** This is not a claim of zero total validation errors.

- PBIR_JSON_FILE_NO_SCHEMA: powerbi/Ecommerce.pbip lacks a $schema declaration.
- PBIR_JSON_FILE_NO_SCHEMA: powerbi/Ecommerce.Report/definition.pbir lacks a $schema declaration.

These two project metadata findings were documented before final QA and were not introduced by dashboard authoring. Neither root file was changed to suppress them.

- PBIR_SCHEMA_UNREACHABLE: the exact existing visualContainer/2.13.0 schema cannot be retrieved; remote visual schema checks are skipped. Existing schema URLs/versions were preserved. Desktop rendering, CLI metadata, local verified structures and manual acceptance support the implemented content, but do not establish complete remote 2.13.0 schema conformance.
- Auxiliary report-page audit tooltip linkage for tables/matrix remains deferred where serialization was unverified, as documented in the research and page notes. No unsupported tooltip structure was invented.
- Historical aggregate exports are disconnected and do not support unrestricted joint filtering. Sales exclude freight; currency remains unconfirmed. Observed returns are not lifetime retention. Extract boundaries, November 2016 coverage gap and incomplete follow-up limit comparisons. Timing shares are conditional on observed repeat customers and cumulative thresholds are not additive. Category memberships overlap and transitions do not establish causal affinity.

## Change control and completion

No presentation fixes were required and no PBIR, model, DAX, relationship, Power Query, data, CSV or accepted definition was changed during final QA. SHA256 checks across 377 existing report/model/data/dashboard files found zero changes.

Every file changed in this final pass:

- docs/powerbi_page4_acceptance.md - marked Page 4 accepted using the user's manual confirmation; preserved earlier implementation history.
- docs/powerbi_final_acceptance.md - this final QA record.

All four pages are accepted. Work stops after final dashboard QA. README, portfolio case study and resume packaging were not started.
