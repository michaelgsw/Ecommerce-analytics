# Page 1 optimization and acceptance

Date: 2026-10-07. Report: Ecommerce.Report. Page: Executive Overview (68ec04fb25bcdce7998c).

Scope: Page 1 only. This note records authoring and validation. After the user manually reloaded the PBIP, a direct Desktop capture was reviewed; the requested visual acceptance checks passed.

## Audit and changes

- Six KPI bindings already existed. Their visual number formats, metric_key predicates, source-record audit Tooltips and scope labels are now explicit.
- KPI targets: Completed Orders 96,478; Unique Completed Customers 93,358; Observed Item Sales 13,221,498.11 source units; AOV 137.04; Observed Repeat Customer Rate 3.00%; Delivered Order Rate 97.02%. Read-only inspection of dashboard_kpis rational components agrees with these targets. All six displayed Desktop values were verified in the screenshot.
- Counts use None and 0 decimals; money uses None and 2 decimals without a currency symbol; rates use None and 0.00%. Model formats and DAX are unchanged. Delivered rate retains the all-order denominator; All Observed Orders is in its tooltip and the 99,441 population is stated visibly.
- Original monthly visual was a horizontal bar. It is now the specified clusteredColumnChart with month / Monthly Chart Sales (source units), categorical axis, Category.showAll true, and ascending Min(month_date) sorting. The model already has month sorted by month_date; no model edit was made.
- Monthly Tooltips expose original raw sales, delivered orders, monthly distinct customers, monthly AOV, coverage and source flags. Source audit confirms chart blanks for 2016-11 and 2018-09/10, plus observed boundary bars for 2016-09 and 2018-08. No blank-to-zero calculation or not-blank filter was introduced.
- Top Categories retains customer_type = All completed and sales_rank <= 10, sorted by Category Sales descending. Readable axis space, two-decimal compact amount labels, exact source-unit tooltip values and fixed full-history title are applied.
- Status remains clusteredBarChart with order_status / Status Order Count, all eight statuses, no population filter, and no incoming cross interactions. Its labels use full counts; operational color is neutral gray.
- The missing Monthly Coverage Detail is implemented as tableEx using the validated Page 2 Values pattern: month, coverage_status, Sum(all_orders), Sum(completed_orders), Sum(item_sales_hundredths), Max(flag_mom_comparable). Totals are disabled. At one row per month these preserve the specified values. Raw sales are explicitly labeled hundredths.
- Purchase month is a local unsynced dropdown in the header. It filters only the monthly chart and coverage table.
- The specification also requires a local category slicer. Added a local unsynced category_display dropdown restricted to All completed. It filters only Top Categories. A nearby note explains that fixed top-10 ranks can leave a lower-ranked selection empty.
- The original interaction array included an unsafe monthly-to-category DataFilter and omitted many pairs. Replaced it with 132 explicit directed interactions for 12 data visuals: 3 allowed DataFilter pairs; all 129 remaining pairs NoFilter.
- Page 2 is the style template: 16px margins/gutters, white rounded 8px containers, DIN business titles, Segoe UI text, 21pt callouts and 12pt labels. Six 108px KPI cards align in one row. Cards budget two label lines with 8px inner/outer padding; completed metrics use restrained teal accents and operational status uses neutral gray.
- Layout: scoped header controls; six KPIs; monthly chart approximately two-thirds width and Top Categories one-third; Status and coverage table below; concise disclosures at the footer.
- All Page 1 JSON text is ASCII. Technical automatic subtitles are disabled. Visible disclosures state historical scope, freight exclusion and source units. Schema URLs are unchanged.

## Supported structure and limitations

Evidence: [dashboard specification](powerbi_dashboard_spec.md), [PBIR research](pbir_authoring_research.md), unchanged Page 2 card/table/slicer/textbox styles, local Page 1 filters and interactions, installed Microsoft CLI metadata.

Verified catalog describe clusteredColumnChart / tableEx; formatting describe-object clusteredColumnChart categoryAxis / valueAxis / labels; clusteredBarChart categoryAxis / dataPoint; cardVisual value / accentBar; tableEx total / columnWidth.

The official [visualConfiguration/2.7.0 comparison schema](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualConfiguration/2.7.0/schema-embedded.json) establishes queryState.<role>.showAll as a boolean and visual-only projection formats. It was inspected read-only through Invoke-RestMethod; no project schema was replaced.

Coverage table's auxiliary boundary/MoM report-page tooltip is deferred: tableEx has no Tooltips role and exact report-tooltip linkage remains unverified. Core coverage columns and safe chart Tooltips are implemented. The 26-month detail table intentionally uses vertical scrolling; displaying every row at once would overcrowd the overview. Other visuals should not need scrolling, pending Desktop inspection.

## Validation and preservation

- powerbi-report-author validate powerbi/Ecommerce.Report: exit 0, zero errors, succeededWithWarnings.
- Only warning: existing visualContainer/2.13.0 schema unreachable, so remote visual JSON-schema validation is skipped. Exact 2.13.0 URLs are preserved; this warning limits exact-schema conformance claims.
- Manual structure checks: all projected model fields exist, queryRefs unique, visuals within the canvas, no non-ASCII text, no synced slicers, exactly three allowed filter interactions.
- SHA-256 comparison: only the 19 Page 1 files below changed; 92 other existing report/model/data/dashboard files remain identical; no files deleted. Page 2, Pages 3/4, DAX, relationships, semantic model, Power Query, source data and dashboard CSVs were not modified.
- Desktop preflight during authoring reported unsaved changes; automatic reload was not attempted. User then confirmed manual reload. A direct Desktop Page 1 capture succeeded and its contents matched the authored state.
- Screenshot inspection: all six expected KPI values and formats verified; cards aligned and evenly sized; titles/subtitles clean; all 26 monthly labels ordered chronologically with gap/unresolved periods blank; categories descending and readable; status all-order counts visible; no broken/blank KPI, overlapping visual, encoding problem or unintended clipping found. The coverage table has intentional vertical scrolling for 26 months, with all required columns visible and no horizontal scrollbar.
- No visual correction was needed. Interactive slicer clicks and tooltip hovers were not automated in this screenshot pass; the exact directed interaction contract and supported tooltip bindings were verified structurally.
- Final requested revalidation after screenshot review: zero errors; only the existing exact-schema retrieval warning remains. Protected-file hashes were rechecked. No Page 3 work was started.
- Temporary validation screenshot files were removed after review.

## Every Page 1 file changed

- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/page.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/0655c915bee53e0c490b/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/1fdf078d374c583c5a9e/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/21fada3361c30f72e158/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/2b07154271d11bd9c425/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/2d2dd1ee31dbd9449e24/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/3ec26f6b15dfdac627fc/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/4b8d9c02d5d96d1fefae/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/6bfb50ee42598085e40c/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/6eaeca7910d4e60ae649/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/75c9aefc9fc7231a6df7/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/8bf080e1ed503477af8b/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/9b09bfa14d27205f1340/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/9f7df6aa236b2c0acad7/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/c8ba688b589e69f7a791/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/d2205f026b349f5b78fd/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/ded6767b64add4d6487b/visual.json` (modified).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/ea0631c50b63d6e3587e/visual.json` (added).
- `powerbi/Ecommerce.Report/definition/pages/68ec04fb25bcdce7998c/visuals/fca230082f638adf470d/visual.json` (modified).
