# Page 3 visual acceptance - Retention & Cohorts

Review date: 2026-10-07. Page ID: 519994619417e94b9588.

**Status: ACCEPTED - user-confirmed manual Power BI Desktop acceptance passed.**

## Final manual Desktop acceptance

The user explicitly accepted Page 3 and reported these manual Desktop results:

- Matrix conditional background colors render correctly.
- 2018-08/M0 = M0 membership.
- 2018-08/M1 = FU.
- Selecting 2018-08 makes the common M1-M3 population unavailable, as expected.
- Cohort visuals respond to the Acquisition cohort slicer.
- Repeat-timing visuals remain unchanged: median = 29.0 days; 30/60/90/180-day shares = 50.55% / 61.12% / 68.12% / 82.86%; interval counts = 829 / 587 / 296 / 196 / 413 / 398 / 82.
- Acquisition cohort slicer was restored to All.

These are user-confirmed manual acceptance results, not agent-operated UI tests. They resolve the previous rendered-color and live-interaction acceptance gaps. Page 3 is accepted and closed to further changes. The earlier implementation/preflight observations below are retained as historical context and do not override this final status.

The two pre-existing missing-$schema project metadata findings remain documented separately; acceptance does not claim they were repaired. No report or model file was edited while recording this acceptance. Page 4 has not been started.

## Current formatting correction

Only the Matrix visual 587419bf98ac037e7cb0 was edited. Its existing objects.values array now contains the verified Microsoft Field value conditional background entry:

- Target property: values.backColor.solid.color.expr.
- Source: Measure, Entity dashboard_cohorts, Property Cohort Cell Background.
- Selector: dataViewWildcard matchingOption 1 (data cells only).
- Selector metadata: dashboard_cohorts.Cohort Cell Text, exactly matching the existing Values projection queryRef.

The current stylePreset remains None. Existing dark text (#242424) is preserved in data cells and headers. The existing visualContainer/2.13.0 schema reference is unchanged.

Verification commands and evidence:

- powerbi-report-author formatting describe-object pivotTable values verifies the backColor conditional slot and the static primary/secondary font-color properties.
- [PBIR authoring research](pbir_authoring_research.md), section 9, records the exact measure-based Matrix selector/expression pattern.
- The installed Microsoft authoring reference conditional-formatting-part-07.md confirms direct Measure expressions for color-returning measures, target-queryRef metadata and InstancesOnly matchingOption 1.
- JSON comparison confirms the sole semantic JSON change is this added formatting entry. Matrix query, row/column/value bindings, sorting, layout, totals, filters and all other properties are unchanged.

Expected colors are supplied by the existing unchanged measure:

- M0: #DCE6F1.
- FU: #E5E7EB.
- CG: #FFF2CC.
- TP: #EDE4F7.
- Measured interior zero: #F3FAF5.
- Positive observed return: existing measure output, including #DDEFE4 / #B9DDCC / #8AC7B8.

## Historical Desktop reload and UI test status

The selected-host preflight command was powerbi-report-author preview powerbi/Ecommerce.Report --host desktop --status.

Desktop instance 30664 returned hasUnsavedChanges=true. No reload or post-change screenshot was attempted. The edited Matrix formatting is on disk and is not yet visually verified. The user must resolve the live unsaved state and reopen the latest powerbi/Ecommerce.pbip without overwriting the disk correction with an older live Matrix definition. After confirmation, resume directly with a fresh Page 3 screenshot.

The installed Computer Use skill was read and its @oai/sky API initialized. Both list_apps and list_windows failed with: Computer Use native pipe is unavailable; failed to connect native pipe; system cannot find the file (os error 2). No input was sent to Power BI Desktop, and no slicer selection or scrollbar movement occurred. The session cannot presently perform the requested live UI tests. A working native Computer Use connection or manual user assistance is required.

## Acceptance evidence before this formatting correction

The preceding fresh screenshot showed:

- Matrix rendering without a field error; M0-M23 visible across the visual without horizontal scrolling.
- Readable visible cohort rows from 2016-09 through 2018-06, with a vertical scrollbar for later rows.
- 2016-09/M1 = 0.00%; 2016-09/M2 = CG; 2018-06/M2 = TP.
- M0 shown as M0 and defined as membership in the legend, without a numeric return rate.
- M1/M2/M3 cards = 0.482% / 0.350% / 0.262%.
- Unfiltered benchmark and dynamic coverage note = 17 cohorts / 68,618 original customers.
- Median = 29.0 days; observed repeat-customer denominator = 2,801.
- Timing windows = 50.55% / 61.12% / 68.12% / 82.86%.
- Interval counts = 829 / 587 / 296 / 196 / 413 / 398 / 82.
- No visible mojibake, technical subtitle, broken business label, overlapping container or clipped business title.

That screenshot showed white Matrix backgrounds. It does not verify the new formatting. The preceding dependency-repair pass verified 2018-08/M1 = FU through a read-only query against the reloaded model, but that bottom row has not yet been visually inspected. All six cohort measures were Ready with no errors after that repair; no DAX was changed in this formatting pass.

Saved Page 3 interactions specify NoFilter from acquisition cohort slicer 84fb0970e2b64e6148c7 to median card 69a558fe97e6ef8cc1a4, timing windows f0fcbea402f928c2afa3, and interval distribution 62a3ff8a082744794cda. The slicer is unsynced and has the six intended cohort-filter targets. These are static-definition checks, not a completed live selection test.

## Historical acceptance checklist - superseded by manual acceptance above

1. With the latest PBIP loaded, capture full Page 3 and verify the distinct M0/FU/CG/TP/zero/positive backgrounds with dark text. Reconfirm visible 2016-09/M1, 2016-09/M2 and 2018-06/M2.
2. Select one eligible cohort, such as 2017-01. Confirm the cohort-size chart and Matrix narrow to that cohort. Expected coverage is 1 eligible cohort / 717 original customers; M1/M2/M3 are approximately 0.279% / 0.279% / 0.139%. These expected values are calculated from the actual exported exact components and are not a live UI test result.
3. Confirm median 29.0, the four cumulative timing shares, and all seven interval counts remain unchanged under that selection.
4. Select 2018-08. Capture Matrix evidence showing M0 membership and M1 = FU. Confirm M1/M2/M3 cards are BLANK and the selected coverage note reports no common M1-M3 coverage. Confirm all repeat-timing visuals remain unchanged.
5. Restore acquisition cohort slicer to All and capture/verify the original unfiltered card values and 17-cohort / 68,618-customer coverage.
6. Mark Page 3 accepted only when the rendered colors, bottom-row evidence and live interaction tests pass. Stop before Page 4.

No permanent visual, page or data filter to 2018-08 was added. No live slicer state was changed by this session.

## Known project metadata issues

Command: powerbi-report-author validate powerbi/Ecommerce.Report.

Result: 2 pre-existing errors and 1 existing warning; no additional validation finding from the Matrix formatting change.

- PBIR_JSON_FILE_NO_SCHEMA: powerbi/Ecommerce.pbip has no $schema declaration.
- PBIR_JSON_FILE_NO_SCHEMA: powerbi/Ecommerce.Report/definition.pbir has no $schema declaration.
- PBIR_SCHEMA_UNREACHABLE: the existing visualContainer/2.13.0 schema URL cannot be fetched, so those remote schema checks are skipped.

Neither metadata file was changed to suppress these findings. Existing schema versions were preserved.

## Changed files and scope

- powerbi/Ecommerce.Report/definition/pages/519994619417e94b9588/visuals/587419bf98ac037e7cb0/visual.json: added conditional background formatting only.
- docs/powerbi_page3_acceptance.md: updated this acceptance record.

No other report visual or page, DAX, model, relationship, filter, Power Query, source-data or dashboard CSV file was edited. Page 4 was not started. No temporary screenshot directory was created during this blocked reload sequence.
