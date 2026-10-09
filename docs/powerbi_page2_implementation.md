# Page 2 implementation — Customer Value & Segmentation

Date: 2026-10-07. Page ID: `70113e560dc08a4fcead`.
Scope: Page 2 only. Desktop review is blocked by unsaved Desktop edits; this document is not an acceptance claim.

## Implemented

17 visuals: V1–V6, V5's two inverse cards, V7's two cards, two dropdown slicers, and five textboxes.
All existing schema declarations are preserved, including visualContainer/2.13.0, page/2.1.0 and pagesMetadata/1.1.0.
The 1920 × 1080 layout inherits Page 1's Fluent2 base theme: white containers, rounded 8px corners, thin gray borders, blue chart palette, DIN titles, Segoe UI values, and 16px spacing.
Cards retain Page 1's 21pt callout and 12pt label typography; explicit 8px outer/inner padding budgets two label lines within 108px.

- V1: clusteredColumnChart; customer_type / Segment Customers; customer-share and additive audit Tooltips.
- V2: clusteredBarChart; customer_type / Segment Sales (source units). Custom detail label references Segment Sales Share, retaining its fixed denominator.
- V3: clusteredColumnChart; two existing weighted measures, visually aliased Sales per customer / Sales per completed order. Tooltips expose their additive ratio components.
- V4: lineChart, linear; 100 pareto_point rows, numeric percentile ascending, percentage Y axis fixed 0–1.
- V5: clusteredColumnChart; pareto_point and highlight_top_group = 1. Two separate cards lock sales_80_threshold; their visual-only formats are count and 0.00%.
- V6: tableEx Values projections, no totals. Every displayed column has a Max(highlight_high_value_one_time) conditional teal background rule using the verified wildcard-plus-metadata selector.
- V7: existing locked full-history measures, also filtered to High-value one-time. Safe card Tooltips expose sales hundredths and customer share. Required descriptive threshold/tenure/history note is visible.
- Segment and customer-type slicers are local and unsynced. Eight directed DataFilter entries target only V1/V2/V3/V6. All remaining directed pairs among the twelve data visuals are explicit NoFilter (132 entries total). Concentration, inverse cards and V7 remain isolated.

## Evidence

[PBIR research](pbir_authoring_research.md), [dashboard specification](powerbi_dashboard_spec.md), and existing Page 1 card/bar/slicer/page structures were used.
Installed powerbi-report-author 0.5.0 catalog and formatting metadata verified clusteredColumnChart, clusteredBarChart, lineChart, tableEx, cardVisual and slicer roles, objects, properties and enums.
Relevant commands: catalog describe <type>; formatting describe-object <type> <object>; formatting effective-properties cardVisual / slicer.
Microsoft's installed Cartesian, table, textbox, expression, filter, card and conditional-formatting references supplied the recorded JSON patterns.

Validation found pre-existing missing root $schema declarations. Only the declarations were added; version 1.0 / 4.0 and all bindings/settings were preserved:
- Ecommerce.pbip: [official pbipProperties/1.0.0](https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json).
- definition.pbir: [official definitionProperties/2.0.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json), also the [Microsoft Learn version 4.0 example](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report#definitionpbir).
These were missing declarations, not replacements or upgrades of existing schema URLs.

## Deferred item

V6's completed_orders / threshold numerator-denominator / observation_date audit tooltip is omitted. tableEx has no Tooltips role, and an exact verified report-tooltip page linkage is unavailable. No tooltip section serialization was invented.

## Validation and preservation

- Initial validation: two pre-existing missing-schema errors and a Page 2 heading-height warning.
- Corrected both missing declarations and heading clearance.
- Latest powerbi-report-author validate powerbi/Ecommerce.Report: exit 0, succeededWithWarnings, zero structural errors.
- Remaining warning: PBIR_SCHEMA_UNREACHABLE for existing visualContainer/2.13.0. Remote visual JSON-schema checks were skipped. CLI success is therefore not proof of exact 2.13.0 schema conformance.
- Projection names, unique queryRefs, canvas boundaries and interaction target sets were checked.
- SHA-256 comparison of 85 pre-existing report/model/data/dashboard files: only the three intended existing report/project files below changed. Page 1, model/TMDL/DAX/relationships/Power Query and source/dashboard data remained unchanged; no files deleted.
- Pages 3 and 4 were not created or modified.
- powerbi-desktop status: connected instance PID 5448, matching Ecommerce.pbip / Ecommerce.Report, hasUnsavedChanges = true.
- Automatic reload is blocked to preserve unsaved in-memory work. No screenshot was used to claim validation of disk edits. Manual resolution and confirmation that the latest PBIR is loaded are required before direct Page 2 capture. Interactive slicer behavior and Desktop rendering remain unverified. Page 2 is not accepted.

## Changed-file list

- `powerbi/Ecommerce.pbip`
- `powerbi/Ecommerce.Report/definition.pbir`
- `powerbi/Ecommerce.Report/definition/pages/pages.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/page.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/017e53cc0d5266521e9e/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/0246353a86b9f0fe7ef0/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/04f912cba38267e3713e/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/22ffef8f525328e011e4/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/23a97e2efda58c6e33c1/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/2e4843ce629d75878611/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/3e015afc4c8b758f8a0f/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/46aed7e31ed8c14dd0a4/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/4a503b858384464f1aba/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/4e28bd022bb9a379d6c4/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/6b99a4dbd2d2bc0c73da/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/730c3cebf4225e60c33c/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/792a88aa5d4a0803628b/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/af0b298b1cbfb5b6f620/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/cc7c62e90c865a8ccc40/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/de2c371b2369ca4672fe/visual.json`
- `powerbi/Ecommerce.Report/definition/pages/70113e560dc08a4fcead/visuals/f976b2076865fef66f06/visual.json`
- `docs/powerbi_page2_implementation.md` (this note).

## Page 2 visual acceptance correction — 2026-10-07

- Disabled auto-generated subTitle on every Page 2 visual; intended static page notes and business titles are preserved.
- V2 amount labels: #,##0.00 source units. Custom share detail: 0.00%, two decimals, detailLabelDisplayUnits = 1D (None); sales share remains in Tooltips.
- V5 percentage axis and labels explicitly use None; percentage labels use 0.00%. Other percentage cards/axes retain None and their existing percentage formats.
- Added visual-only friendly field display names. Bindings, measures, filters, interactions, values and layout are unchanged.
- CLI validation: zero errors; existing visualContainer/2.13.0 unreachable warning remains, schema URL preserved.
- Hash comparison: only 17 Page 2 visual.json files changed; all other 86 baseline report/model/data/dashboard files unchanged; no files added/deleted in those protected trees.
- Desktop preflight: matching instance 5448, hasUnsavedChanges = true. Reload blocked; corrected-file screenshot and visual acceptance remain pending manual resolution and confirmation that the latest PBIP is loaded.

## Desktop follow-up — 2026-10-07 (21:49–21:52 EDT)

After user confirmed reload, a direct Page 2 capture succeeded. Inspection still showed original 0.0M% share labels, automatic field-list subtitles and a table vertical scrollbar. Disk inspection confirmed the previously added overrides and root declarations were absent; current files had been rewritten by Desktop. The capture therefore did not pass acceptance.

Reapplied the presentation overrides to the current Page 2 files, with detailLabelDisplayUnits = None, detailLabelPrecision = 2 and percentage format 0.00%. Repeated the visual-only friendly aliases; tightened table grid rowPadding from 8 to 4. Restored the same two missing root schema declarations required by CLI validation; no schema URLs or content versions were upgraded. Layout, bindings, filters, interactions and measure logic are preserved.

Validation after restoration: zero errors, only the existing visualContainer/2.13.0 unreachable warning. Hash comparison against this follow-up baseline: 17 Page 2 visuals plus the two required root declarations changed; all other report/model/data/dashboard files unchanged, no deletions.

Desktop preflight now resolves matching instance 30664 but hasUnsavedChanges = true. Automatic reload was not attempted. Corrected-state screenshot review remains pending: close the older in-memory report without saving it over the disk corrections, reopen the corrected PBIP, and confirm. The next operation should be direct Page 2 capture, with no repeat status/reload/edit before that capture. Temporary validation images are removed.
