# PBIR authoring research — Riverside E-commerce

Research date: 2026-10-07. Scope: research only, compared with [dashboard specification](powerbi_dashboard_spec.md). No report, semantic-model, DAX, relationship, or source-data edits were made.

## Decision

**The missing local line/table/matrix examples are no longer an authoring blocker.** Microsoft CLI metadata and Microsoft references support the six requested visual types, visual filters, directed interactions, matrix field-value colors, and table data bars.

**Core visuals on Pages 2, 3, and 4 can be encoded using evidence A/B/C below. Full specification completion cannot yet be claimed without qualification.** The saved visualContainer/2.13.0 schema is not publicly retrievable in this research session, and the exact report-tooltip page linkage encoding is not established by the installed CLI (its section property is typed unknown). These are specific validation/auxiliary-tooltip gaps, not reasons to reject the core chart/table/matrix work. Rendered correctness remains a later implementation acceptance check.

- A: an existing local PBIR example.
- B: Microsoft documentation/schema/reference.
- C: installed powerbi-report-author CLI metadata.

No report was scaffolded, opened, reloaded, validated, refreshed, or published during research. The requested tool versions and metadata commands were run. Version commands do not establish the version of the Power BI Desktop application itself.

## Tools and evidence precedence

Verified:

```text
powerbi-report-author --version
0.5.0

powerbi-desktop --version
1.0.0
```

The authoring CLI is Microsoft's installed @microsoft/powerbi-report-authoring-cli 0.5.0; its installed metadata provider is @microsoft/powerbi-core-visual-schema 0.1.1. The CLI package identifies Microsoft Corporation as author and microsoft/skills-for-fabric as its repository.

Live research followed the requested source priority: Microsoft Learn; exact project schema URLs; microsoft/skills-for-fabric; Microsoft samples/schema repositories. No blog/forum PBIR was used. CLI metadata takes precedence over examples for visual types, role kinds, properties, selectors, and enums. Microsoft references supply structural patterns the catalog does not expose. The catalog itself reports roles, not a full queryState JSON template.

Important discrepancies resolved in favor of actual metadata/schema:

- An older Cartesian reference mentions a Gradient role for bar/column charts. Installed clusteredColumnChart metadata does not list it. Do not add it.
- An installed table reference says tableEx values lacks fontColor. CLI 0.5.0 does expose values.fontColor; use CLI metadata. Static text uses fontColorPrimary/Secondary; conditional text uses fontColor.
- QueryAggregateFunction 2 is **Distinct count** in the official semantic-query schema, despite a reference abbreviating it as Count. Function 5 counts non-null values.
- describe-object <type> general returns the shared VCO when its name collides with a visual object. Use formatting effective-properties <type> and inspect visualObjects.general for the visual's own properties. This was verified for pivotTable and slicer.
- Metadata type unknown means the property name is established, but its nested serialization is not documented by that command. Do not invent children from the property name.

## Exact existing project schemas

Preserve these exact URLs for subsequent project work:

- [visualContainer/2.13.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json): every existing visual.json.
- [page/2.1.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json): existing page.json.
- [pagesMetadata/1.1.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json): pages.json.
- [report/3.3.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json): definition/report.json.
- [versionMetadata/1.0.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json): version.json.

definition.pbir has version 4.0 and a byPath binding to ../Ecommerce.SemanticModel; it currently has no $schema. Do not add one or change that binding as part of this research.

The exact page, report, pagesMetadata, and versionMetadata schemas were retrievable. The exact visualContainer/2.13.0 URL returned HTTP 404 using Invoke-WebRequest; its raw Microsoft GitHub counterpart also returned 404. The [Microsoft schema mirror inventory](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition/visualContainer) contained visual versions through 2.12.0 and no 2.13.0 folder at inspection time.

For structural comparison only, the official [visualContainer/2.12.0 schema](https://raw.githubusercontent.com/microsoft/json-schemas/main/fabric/item/report/definition/visualContainer/2.12.0/schema.json) and its [visualConfiguration/2.7.0 dependency](https://raw.githubusercontent.com/microsoft/json-schemas/main/fabric/item/report/definition/visualConfiguration/2.7.0/schema-embedded.json) were inspected. **Neither version is an instruction to change the project.** They corroborate the existing envelope/query/projection/sort patterns; they cannot certify 2.13.0 compatibility.

Dependencies fetched from developer.microsoft.com through the existing page/report schemas:

- [filterConfiguration/1.3.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/filterConfiguration/1.3.0/schema-embedded.json).
- [semanticQuery/1.4.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/semanticQuery/1.4.0/schema.json).
- [formattingObjectDefinitions/1.5.0](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/formattingObjectDefinitions/1.5.0/schema.json).

These dependency versions are references, not new root $schema values for project files.

## Local examples inspected

Current report: powerbi/Ecommerce.Report. Only Executive Overview is present in pages.json.

Examples under definition/pages/68ec04fb25bcdce7998c:

- cards: visuals/75c9aefc9fc7231a6df7/visual.json and five other cardVisual files.
- horizontal bars and explicit sorting: visuals/8bf080e1ed503477af8b/visual.json.
- categorical and advanced visual filters: the same category bar, with customer_type = All completed and sales_rank <= 10.
- slicer: visuals/4b8d9c02d5d96d1fefae/visual.json.
- interactions and 1920 × 1080 canvas: page.json, with DataFilter and NoFilter entries.

All saved PBIR JSON was read. All nine model table TMDL files were inspected for names; relevant measure bodies and formats were read. All named measures required by Pages 2–4 exist, including Cohort Cell Text, Cohort Cell Background, the pooled M1–M3 rates, inverse Pareto cards, and repeat timing measures. No replacement measures or inline DAX are needed for core visuals.

## Shared query, projection, sort, and expression patterns

Sources: local bars/cards/slicer (A), installed CLI roles (C), Microsoft expressions/Cartesian/table references and comparison schema (B).

A role maps to an object containing projections, not a bare array:

```json
{
  "queryState": {
    "<CLI role name>": {
      "projections": [
        {
          "field": {
            "Measure": {
              "Expression": { "SourceRef": { "Entity": "<exact TMDL table>" } },
              "Property": "<exact TMDL measure>"
            }
          },
          "queryRef": "<table>.<measure>",
          "nativeQueryRef": "<measure>"
        }
      ]
    }
  }
}
```

For a grouping column, replace Measure with Column. Query bindings use SourceRef.Entity. Measures are referenced directly; do not wrap measures in Aggregation. For a raw aggregated column, use Aggregation with Expression.Column and a documented Function; queryRef should identify that aggregation consistently, e.g. Max(Table.flag).

Required projection fields in the comparison schema are field and queryRef. Include nativeQueryRef using the Microsoft reference pattern, unique within the visual. Optional displayName provides visual-only aliases, e.g. V3's Sales per customer and Sales per completed order; it does not rename the measure. Optional format can provide presentation-only formatting where a model measure lacks it. active is used for drill state; do not construct an unnecessary hierarchy for these single-level visuals.

Sorting is a sibling of queryState inside visual.query:

```json
{
  "sortDefinition": {
    "sort": [
      { "field": { "<Column/Measure/Aggregation>": {} }, "direction": "Ascending" }
    ],
    "isDefaultSort": false
  }
}
```

The placeholder field above must be replaced by a complete semantic expression. Directions are Ascending/Descending strings here. Do not confuse them with semantic-query OrderBy.Direction numeric values 1/2.

For text labels ordered by another column, Microsoft Learn explicitly supports adding the sort column to Tooltips and sorting by it. Use a documented aggregated sort expression, e.g. Min(sort_order), where each category has one sort key, and the same expression in sortDefinition. Confirm actual axis order in Desktop. This supports R5/R6/P3 without changing DAX or model sort metadata. cohort_month is an ISO month label; ascending label order is chronological, but R1 can also expose Min(cohort_date) as the sort key to match the spec. The existing model only declares sortByColumn on dashboard_monthly_sales[month], not cohort_month, metric, or behavior_display. Do not assume those other sortByColumn settings exist. [Microsoft sorting guidance](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-sort-by-column).

CLI expression codec checks:

```text
powerbi-report-author expr encode --kind bool false
=> {"expr":{"Literal":{"Value":"false"}}}
powerbi-report-author expr encode --kind integer 0
=> {"expr":{"Literal":{"Value":"0L"}}}
powerbi-report-author expr encode --kind number 1
=> {"expr":{"Literal":{"Value":"1D"}}}
powerbi-report-author expr encode --kind string Dropdown
=> {"expr":{"Literal":{"Value":"'Dropdown'"}}}
powerbi-report-author expr encode --kind color '#E5E7EB'
=> {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E7EB'"}}}}}
```

Boolean formatting values, numeric formatting values, string enums, and colors use these PBIR wrappers. Do not copy plain theme JSON values into visual.objects. A numeric-looking enum must be encoded according to the documented property's semantics, not automatically as a quoted string.

## 1. lineChart

- PBIR visualType: lineChart.
- Required roles: Category (Grouping), Y (Measure).
- Optional roles: Series (Grouping, maximum 1), Y2 (Measure), Rows (Grouping), Tooltips (Measure).
- queryState: Category.projections = grouping column(s); Y.projections = existing measure(s); optional Tooltips.projections = measures or aggregated columns. For V4 use one Category and one Y projection; omit Series/Y2/Rows.
- Required project projections: dashboard_customer_concentration[target_customer_percent] as Column; [Pareto Sales Share] as Measure.
- Sorting: ascending target_customer_percent; isDefaultSort false. Keep X labels 1–100 as numbers, not percentage fractions.
- Important objects: categoryAxis, valueAxis, lineStyles, markers, labels, legend, dataPoint. valueAxis.start/end support the 0–1 range for a percentage measure. lineStyles.lineChartType enum is linear/smooth/step; use linear for the precomputed Pareto points. strokeWidth, strokeColor, showMarker, markerShape and markerSize are verified properties.
- Filters: record_type = pareto_point; no concentration-to-other or incoming segment/type interactions.
- Sources: Microsoft Cartesian/expressions references; CLI; common query/sort envelope matches local bars.
- Commands verified: catalog describe lineChart; formatting list-objects lineChart; formatting describe-object lineChart categoryAxis; formatting describe-object lineChart valueAxis; formatting describe-object lineChart lineStyles.

## 2. clusteredColumnChart

- PBIR visualType: clusteredColumnChart (ordinary single-series columns can use this type too).
- Required roles: Category (Grouping), Y (Measure).
- Optional roles: Series (Grouping, maximum 1), Rows (Grouping), Tooltips (Measure).
- queryState: Category.projections plus Y.projections; two Y measures produce V3's two measure series without a fabricated legend table or a Series column.
- Required project projections: V1 customer_type / Segment Customers; V3 customer_type / Average Customer Sales (source units) and Segment AOV (source units); V5 target_customer_percent / Pareto Sales Share; R1 cohort_month / New Cohort Customers; R5 metric / Repeat Window Share; R6 metric / Repeat Interval Count.
- Sorting: V5 numeric percentile ascending; R1 cohort date ascending; R5/R6 ascending Min(sort_order) also projected to Tooltips. V1/V3 may use customer_type ascending since no alternate ordering is specified.
- Important objects: categoryAxis, valueAxis, dataPoint, labels, legend. labels.labelPosition includes Auto/InsideEnd/OutsideEnd/InsideCenter/InsideBase/Above/Under. legend.position includes Top/TopCenter/Bottom etc. Enable legend for V3 and use projection displayName for the specified measure labels; omit legend for one-series comparisons. Do not use defaultColor to flatten multiple series to one color.
- Sources: CLI and Microsoft Cartesian references; shared envelope from local bars.
- Commands verified: catalog describe clusteredColumnChart; formatting list-objects clusteredColumnChart; formatting describe-object clusteredColumnChart labels; formatting describe-object clusteredColumnChart legend.

## 3. tableEx

- PBIR visualType: tableEx.
- Required role: Values (GroupingOrMeasure). No Rows, Columns, or Tooltips role.
- queryState: Values.projections in display-column order; grouping columns and measures share the same role.
- Required V6 projections: segment Column; Segment Customers, Segment Customer Share, Segment Sales (source units), Segment Sales Share, Average Customer Sales (source units), Segment AOV (source units) as Measure projections.
- Required P1 projections: category_display Column; Category Sales (source units), Category Sales Share, Category Order Count as Measure; items_sold as Sum aggregation; product_category_name and product_category_name_english as Column projections. Retain blank labels faithfully. Do not aggregate category scopes together.
- Sorting: V6 can use segment ascending; P1 sales descending, then category_display for a stable tie order. Do not add a Top N restriction to P1.
- Important objects: columnHeaders, values, columnFormatting, columnWidth, grid, total. columnHeaders.autoSizeColumnWidth true plus columnAdjustment growToFit is the Microsoft default pattern; verified alternatives are fitToContent/growToFit/fixedWidth. total.totals false disables totals; recommended for these detail tables.
- V6 accent: values.backColor conditional rule, testing Max(highlight_high_value_one_time) == 1, targeting a displayed column's queryRef with a values-only wildcard. Repeat the entry for each displayed column if the whole row is accented. Raw flag is not summed. No new color measure is necessary.
- P1 data bars: columnFormatting.dataBars with a metadata-only selector targeting Category Sales (source units); details below.
- Sources: Microsoft table and conditional-formatting references; CLI.
- Commands verified: catalog describe tableEx; formatting list-objects tableEx; formatting describe-object tableEx columnHeaders; formatting describe-object tableEx values; formatting describe-object tableEx columnFormatting; formatting describe-object tableEx total.

## 4. pivotTable / Matrix

- PBIR visualType: pivotTable. Use this documented matrix type; do not substitute tableEx or invent a heatmap custom visual.
- CLI required role: Values (Measure). Rows and Columns are optional Grouping roles in the general catalog, but **both are required for the planned cohort layout**.
- queryState: Rows.projections = cohort_month Column; Columns.projections = month_index Column; Values.projections = Cohort Cell Text Measure.
- Required color expression: existing Cohort Cell Background Measure in objects.values[].properties.backColor.solid.color.expr. It is a formatting expression, not a second visible Values projection and not a raw text column in a measure-only role.
- Sorting: Rows/cohort_month ascending and numeric Columns/month_index ascending. Keep M0–M23. Do not add a primary numeric-rate not-blank filter: the text measure intentionally preserves FU/CG/TP cells.
- Important objects: values, columnHeaders, rowHeaders, subTotals, grid, columnWidth, columnFormatting, rowTotal, columnTotal, total. values.valuesOnRow false keeps the values in columns. Static dark text uses values.fontColorPrimary/Secondary.
- subTotals has rowSubtotals/columnSubtotals booleans, perRowLevel/perColumnLevel and levelSubtotalEnabled. CLI selector hints are Row and Column, encoded as selector.id. Set rowSubtotals and columnSubtotals false on their corresponding instances; verify no totals or subtotal bands remain. rowTotal and columnTotal are formatting objects, **not** places to invent show flags; they expose fonts/fills/applyToHeaders. If a grand-total band persists, capture Desktop's saved encoding instead of adding an unlisted property.
- Sources: Microsoft table/conditional-formatting references, formatting selector schema, CLI; model contains both existing cell measures.
- Commands verified: catalog describe pivotTable; formatting list-objects pivotTable; formatting describe-object pivotTable values; formatting describe-object pivotTable columnHeaders; formatting describe-object pivotTable rowHeaders; formatting describe-object pivotTable subTotals; formatting describe-object pivotTable rowTotal; formatting describe-object pivotTable columnTotal; formatting effective-properties pivotTable; formatting describe-object pivotTable visualTooltip.

## 5. cardVisual

- PBIR visualType: cardVisual.
- Required role: Data (Measure), **not Values or Fields**.
- Optional roles: Rows (Grouping), Tooltips (Measure).
- queryState: Data.projections containing one existing measure for each separate card. Tooltips may contain measures or correctly aggregated audit fields. Do not create extra category Rows for these standalone cards.
- Required projections: V5 inverse 80% measures; V7 High Value One-Time Customers / High Value One-Time Sales Share; R2 M1/M2/M3 Return Rate and eligible-count/coverage measures; R4 Median Days to Second Purchase.
- Sorting: no meaningful sort for one measure/one card; omit or retain the local one-measure sort pattern. Do not sort cards as a data series.
- Important objects: value, label, layout, padding, fillCustom and VCO title. value has selector hint default: selector {"id":"default"}. Verified value properties include fontSize, fontColor, labelDisplayUnits, labelPrecision, customFormatString and showBlankAs. Keep BLANK distinguishable from zero. Count and percentage display overrides can be scoped to the visual without changing DAX.
- Sources: six local cardVisual files, CLI, Microsoft card/expressions references.
- Commands verified: catalog describe cardVisual; formatting list-objects cardVisual; formatting describe-object cardVisual value.

## 6. slicer

- PBIR visualType: slicer.
- Required role: Values (Grouping). No Tooltips role for this classic type.
- queryState: Values.projections = one Column projection for each planned local slicer.
- Required projections: Page 2 dashboard_customer_segments[segment] and [customer_type]; Page 3 dashboard_cohorts[cohort_month]; Page 4 dashboard_categories[category_display] and [customer_type].
- Sorting: ascending the displayed field where appropriate; no hierarchical projections or expansion state are needed.
- Important objects: data, selection, header, items, general; VCO title and padding. data.mode Dropdown/Basic are documented patterns and metadata includes additional modes (VerticalList, HorizontalList, Between, Before, After, Relative, Single, RelativeTime, RelativeDatePicker). selection.strictSingleSelect forces one choice; singleSelect means multi-select with CTRL, not strict single selection.
- Restrict Page 4 customer-type options with a visual filter to One-time/Repeat. Omit visual.syncGroup for page-local slicers. Set directed page interactions explicitly.
- Current selection lives in the visual's objects.general.filter semantic filter pattern; filterConfig limits the slicer's available data. Do not confuse selection state with a restriction on available options. No initial selection is needed unless the spec requires it.
- If a slicer gets per-visual VCO formatting, declare its padding explicitly per Microsoft's slicer reference.
- Sources: local slicer, Microsoft slicer/expressions references, CLI.
- Commands verified: catalog describe slicer; formatting list-objects slicer; formatting describe-object slicer data; formatting describe-object slicer selection; formatting effective-properties slicer.

## 7. Visual-level filters

Place filterConfig beside visual at the visual.json root. Do not put it inside visual.query or apply a page filter when only some visuals should be restricted.

A concrete categorical filter for V4, adapted from the existing saved category filter:

```json
{
  "name": "<unique-filter-name>",
  "field": {
    "Column": {
      "Expression": { "SourceRef": { "Entity": "dashboard_customer_concentration" } },
      "Property": "record_type"
    }
  },
  "type": "Categorical",
  "filter": {
    "Version": 2,
    "From": [
      { "Name": "d", "Entity": "dashboard_customer_concentration", "Type": 0 }
    ],
    "Where": [
      {
        "Condition": {
          "In": {
            "Expressions": [
              {
                "Column": {
                  "Expression": { "SourceRef": { "Source": "d" } },
                  "Property": "record_type"
                }
              }
            ],
            "Values": [[{ "Literal": { "Value": "'pareto_point'" } }]]
          }
        }
      }
    ]
  },
  "howCreated": "User"
}
```

Top-level field uses Entity; predicate SourceRef uses the From alias Source. Numeric flags can use In with integer literals 0L/1L. Multi-choice uses multiple one-value tuples, e.g. One-time/Repeat. Distinct filter records are combined to restrict the visual; unique names should be used across the report.

Advanced ComparisonKind: 0 equals, 1 greater, 2 greater-or-equal, 3 less, 4 less-or-equal. The local sales_rank <= 10 filter demonstrates Function-independent integer filtering. A placeholder filter entry with only field/type has no predicate; it does not enforce an eligibility condition.

isLockedInViewMode true may protect fixed scope predicates; it is a plain JSON metadata boolean, distinct from expression-wrapped formatting booleans.

Sources: local 8bf080e1ed503477af8b visual, official filterConfiguration/1.3.0 and semanticQuery/1.4.0 schemas, Microsoft filters/expressions references. CLI inspection surface: preview-filters exists in --help; predicates were read directly from local files. The CLI has no dedicated filter-construction metadata command.

## 8. Visual interactions

Stored in page.json.visualInteractions, not in visual.objects:

```json
{
  "source": "<source visual name>",
  "target": "<target visual name>",
  "type": "DataFilter"
}
```

Exact page/2.1.0 schema enums: Default, DataFilter, HighlightFilter, NoFilter. Use DataFilter for allowed slicer targets and NoFilter for every other applicable target. Direction is significant; write the reverse direction separately if needed. Do not assume that disconnected tables alone enforce all requested behavior.

Page contract:

- Page 2 segment/type slicers -> V1, V2, V3, V6: DataFilter. -> V4, V5 and inverse cards, V7: NoFilter. Chart/table cross interactions: NoFilter unless expressly required by the spec.
- Page 3 acquisition cohort slicer -> R1, R2 cards and eligible counters/coverage note, R3: DataFilter. -> R4/R5/R6: NoFilter. Other chart cross interactions: NoFilter.
- Page 4 category slicer -> P1/P2: DataFilter; -> P3: NoFilter. Customer-type slicer -> P2 only: DataFilter; -> P1/P3: NoFilter. Chart cross interactions: NoFilter.
- Slicer-to-slicer filtering is not specified as an allowed target; use NoFilter when enforcing the literal listed-target contract.
- Keep local slicers unsynced. drillFilterOtherVisuals does not replace the directed selection interaction array.

Sources: existing page.json and its exact official schema; [Microsoft interaction documentation](https://learn.microsoft.com/en-us/power-bi/create-reports/service-reports-visual-interactions). CLI catalog does not own the page interaction enum; the exact page schema does.

## 9. Matrix conditional formatting and table cell formatting

### R3 field-value background

The complete entry below goes in visual.objects.values. It uses the existing color measure directly and targets the **text measure's queryRef**:

```json
{
  "properties": {
    "backColor": {
      "solid": {
        "color": {
          "expr": {
            "Measure": {
              "Expression": { "SourceRef": { "Entity": "dashboard_cohorts" } },
              "Property": "Cohort Cell Background"
            }
          }
        }
      }
    }
  },
  "selector": {
    "data": [{ "dataViewWildcard": { "matchingOption": 1 } }],
    "metadata": "dashboard_cohorts.Cohort Cell Text"
  }
}
```

Both data wildcard and metadata are required for table/matrix value-driven cell colors. matchingOption 1 targets instances only; 0 includes totals; 2 targets totals only. The selector metadata must exactly match the projection queryRef. Do not use the color measure's queryRef as the target.

No invented fieldValue property, colorRule object, or color measure aggregation is required. Use values.backColor for conditional color and values.backColorPrimary/Secondary for static banding. Set stylePreset VCO name to None when applying custom cell/header colors, following Microsoft's table reference; confirm its effect visually.

The existing color measure returns the requested FU/CG/TP/M0/zero/positive green palette. Leave its logic unchanged. Keep all cells and disable totals. Check 2016-09/M1 measured zero, 2016-09/M2 CG, 2018-06/M2 TP, and 2018-08/M1 FU in Desktop after implementation. [Microsoft field-value formatting guidance](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-conditional-table-formatting).

### V6 highlight

Use values.backColor.solid.color.expr.Conditional.Cases with a ComparisonKind 0 test on Aggregation(Max(flag), Function 4), integer 1L, and a teal color literal. This operates at segment row grain; no DAX edit is needed. Use the same wildcard-plus-metadata selector pattern for each displayed column that should be accented. The teal hue is a design choice, not an invented PBIR structure.

### P1 data bars

Use a columnFormatting entry, not values:

```json
{
  "properties": {
    "dataBars": {
      "positiveColor": {
        "solid": { "color": { "expr": { "Literal": { "Value": "'#118DFF'" } } } }
      },
      "negativeColor": {
        "solid": { "color": { "expr": { "Literal": { "Value": "'#D64554'" } } } }
      },
      "axisColor": {
        "solid": { "color": { "expr": { "Literal": { "Value": "'#999999'" } } } }
      },
      "reverseDirection": { "expr": { "Literal": { "Value": "false" } } },
      "hideText": { "expr": { "Literal": { "Value": "false" } } }
    }
  },
  "selector": {
    "metadata": "dashboard_categories.Category Sales (source units)"
  }
}
```

Data bars use metadata-only selectors. Do not add dataViewWildcard. Keep numeric sales text visible. Colors shown are Microsoft's reference defaults, not a locked report design. Omit minValue/maxValue for automatic scale; a fixed scale needs both documented numeric bounds.

Sources: CLI tableEx.columnFormatting and pivotTable.values; official selector and semantic-query schemas; Microsoft conditional-formatting parts 5, 6 and 7. dataBars is typed unknown by CLI; its children and selector pattern come from Microsoft's authoring reference, not conjecture.

## Supplementary visual mechanics required by the spec

### Horizontal bars

Existing clusteredBarChart examples plus catalog describe clusteredBarChart support Category/Y, optional Series (max 1), Rows and Tooltips. Use Category customer_type and Y Segment Sales for V2; Category category_display / Y Category Sales Share / Series customer_type for P2; Category behavior_display / Y First-to-Second Transition Share for P3.

V2's labels must use the existing Segment Sales Share as custom detail, not the built-in percent-of-visible-total, because the spec's denominator is fixed. CLI labels exposes showDynamicLabels, dynamicLabelDetail, detailContentType, enableDetailDataLabel, detailCustomFormatString and labelContentLayout. Microsoft Cartesian part 2 documents expression-backed dynamic details and a dataViewWildcard selector. Keep source-unit sales as the main value and format the detail as a percentage. Verify the final label in Desktop.

### Static page text

catalog describe textbox reports no required roles. Microsoft textbox reference uses visual.objects.general[].properties.paragraphs as a native array, with textRuns[].value plain strings and textStyle. This supports the specified titles, history/scope disclaimers, heatmap legend and definition notes. Do not turn paragraphs into an expression/stringified JSON value.

### Tooltips: supported approaches and remaining gap

Chart/card Tooltips roles accept measures or aggregations, not arbitrary grouping-only fields. Use SUM only for additive counts/components; MAX for repeated fixed denominators; MIN/MAX for a flag/text field only when the visual grain guarantees a single value, otherwise use an existing context-safe measure or a report tooltip page that displays the raw rows.

**tableEx/pivotTable have no Tooltips role.** Do not add one to queryState. Their audit tooltip fields need a report tooltip page or a consciously revised visible detail layout; adding extra Values columns would change the specified display and, for a matrix, could add unwanted subcolumns.

Microsoft Learn supports manually assigned report tooltip pages. Exact page/2.1.0 supports type Tooltip, visibility HiddenInViewMode, and pageBinding type Tooltip. CLI visualTooltip VCO supports show, type Default/Canvas, and section (Page, type unknown). This establishes the supported route, but not the exact serialized section value and full context-binding contract for this project. No example of that linkage was found in the local report or loaded Microsoft authoring references. **Do not present an invented section expression as verified.** Capture a Microsoft/Desktop-produced tooltip-page link or find a concrete official example before implementing the V6/R3/P1 auxiliary tooltips.

A hidden tooltip page can retain the four visible report pages. Its filters must respect V6 segment context, R3 cohort/month cell context and P1 All completed/category context. R2 returning-count tooltips need exactly the same common-coverage filters as their cards; eligible cohort/customer counters should retain their M0 definition rather than blindly inherit a card's month_index = 1/2/3.

Sources: [Microsoft report tooltips](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-tooltips), exact page schema, formatting describe-object pivotTable visualTooltip, formatting describe-property pivotTable visualTooltip section.

## Gap analysis against Pages 2, 3, and 4

These statuses distinguish a supported authoring recipe from a rendered, accepted report. Nothing below was implemented.

### Page 2 — Customer Value & Segmentation

- **V1: supported (B/C).** clusteredColumnChart, customer_type Category, Segment Customers Y; segment/type slicer targets established.
- **V2: supported (A/B/C), render check required.** clusteredBarChart with source-unit sales; custom detail uses Segment Sales Share and fixed denominator. Do not substitute percent-of-visible-total labels.
- **V3: supported (B/C).** two Y measure projections and displayName aliases; existing weighted measures already match the spec.
- **V4: supported (B/C).** lineChart with 100 numeric percentile categories, Pareto Sales Share, pareto_point filter, ascending sort, fixed scope.
- **V5: supported (A/B/C).** clusteredColumnChart with highlight_top_group = 1 and pareto_point, plus separate inverse cards restricted to sales_80_threshold. Do not sum cumulative shares.
- **V6: core table/accent supported (B/C); extra audit tooltip linkage unresolved.** Values projections and Max(flag) conditional formatting are established.
- **V7: supported (A/B/C).** two existing locked measures, segment = High-value one-time visual filter, NoFilter incoming interactions and explanatory textbox.
- **Page-level result:** core visual construction no longer requires guessing. Full fidelity depends on the shared exact-schema validation issue and V6's auxiliary tooltip encoding.

### Page 3 — Retention & Cohorts

- **R1: supported (B/C).** clusteredColumnChart, M0 filter, acquisition slicer, New Cohort Customers, date/key sorting.
- **R2: supported (A/B/C).** separate M1/M2/M3 Data projections; each card has month_index 1/2/3, insufficient coverage = 0, coverage_status = interior_observed. Existing measures enforce the common population. Eligible-count and coverage-note cards use their existing M0-based measures with matching acquisition selection. No DAX edits.
- **R3: core matrix/color supported (B/C); auxiliary audit tooltip linkage unresolved; totals require rendering verification.** Rows/Columns/Values and field-value color selector are established. Do not filter out unavailable-rate cells. No undocumented rowTotal.show or general.rowGrandTotal flags.
- **R4: supported (A/C).** existing median card measure and summary/median scope; no cohort interactions.
- **R5: supported (B/C).** clusteredColumnChart; record_type summary, scope first_to_second, metric in the four within_*_days values; sort via Min(sort_order) in Tooltips. Do not stack or sum overlapping windows.
- **R6: supported (B/C).** clusteredColumnChart; interval_bin and first_to_second; metric categories ordered by sort_order. Omit the optional scope switch unless its dynamic title/denominator behavior is fully specified.
- **Page-level result:** main retention visuals can be encoded from evidence; full fidelity still needs R3 tooltip linkage, exact-schema validation and matrix render/acceptance checks. No need to change DAX, relationships or source data.

### Page 4 — Product & Category Performance

- **P1: core table/data bars supported (B/C); auxiliary audit tooltip linkage unresolved.** customer_type All completed, all category groups, no Top N, source labels/translation fields separate, totals disabled.
- **P2: supported (A/B/C).** clusteredBarChart with category Category, customer_type Series, Category Sales Share Y; One-time/Repeat visual filter. Category and local type slicers target only the listed visuals.
- **P3: supported (A/B/C).** clusteredBarChart with four behavior_display classes and Transition Share; Min(sort_order) tooltip sort; every incoming slicer and cross interaction NoFilter.
- **Page-level result:** all main visuals have supported recipes. Complete P1 tooltip fidelity and exact-schema validation remain open.

### What remains before a claim of complete, guess-free implementation

1. Resolve exact visualContainer/2.13.0 schema availability, or report its validation unavailability explicitly while using A/B/C evidence for the content. Preserve 2.13.0; do not silently downgrade to 2.12.0 or copy the reference's 2.9.0 root.
2. Establish a concrete official/Desktop-produced report-tooltip page link for table/matrix audit fields. CLI's unknown section type alone is not sufficient proof of its serialization.
3. After a later authorized implementation, run normal validation and inspect schema-unreachable diagnostics. An overall success with schema checks skipped is not proof of exact-schema conformance.
4. Load the latest report into Desktop, review each affected page, test custom labels/sort keys/tooltip context, ensure matrix totals are absent, and execute the spec's filter-isolation and numerical acceptance checks.

Items 1–2 are research/validation coverage gaps. Item 4 is normal implementation verification and cannot be completed by reading schemas. None is a request to create relationships, modify measures, or regenerate data.

## Sources and verification log

Microsoft Learn:

- [Power BI project report folder / PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report): external editing and schema-based report organization.
- [Conditional table formatting](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-conditional-table-formatting): field colors and data bars.
- [Visual interactions](https://learn.microsoft.com/en-us/power-bi/create-reports/service-reports-visual-interactions).
- [Sort by another column](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-sort-by-column).
- [Report tooltip pages](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-tooltips).

Microsoft authoring reference base:
https://github.com/microsoft/skills-for-fabric/tree/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring

Read locally under .agents/skills/powerbi-report-cli and cross-checked key live files:

- [Cartesian query bindings](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/cartesian.md).
- [Custom labels and axes](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/cartesian-part-02.md).
- [Tables/matrices](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/table.md).
- [Expressions and sorting](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/expressions.md).
- [Data bars](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/conditional-formatting-part-06.md).
- [Field-value colors](https://github.com/microsoft/skills-for-fabric/blob/main/plugins/powerbi-authoring/skills/powerbi-report-cli/references/authoring/conditional-formatting-part-07.md).
- Additional installed references read: filters.md, slicers.md, conditional-formatting.md and part 5, textbox.md, authoring.md and the skill dispatcher.

Microsoft sample repositories inspected for provenance/context:

- [powerbi-desktop-samples](https://github.com/microsoft/powerbi-desktop-samples): Desktop samples and theme schemas. No arbitrary PBIX JSON extraction was needed to support the core recipes.
- [PowerBI-Developer-Samples](https://github.com/microsoft/PowerBI-Developer-Samples): developer samples; not treated as the core built-in visual role authority.
- [Microsoft schema mirror](https://github.com/microsoft/json-schemas): exact version inventory and comparison-only schema.
- Installed core visual schema package metadata points to microsoft/PowerBI-visuals; the attempted public repository tree lookup returned 404. The installed CLI/provider data remains directly inspectable.

Additional commands run:

```text
powerbi-report-author catalog list
powerbi-report-author --help
powerbi-report-author formatting --help
powerbi-report-author expr --help
powerbi-report-author expr encode --help
powerbi-report-author catalog describe clusteredBarChart
powerbi-report-author catalog describe textbox
powerbi-report-author formatting describe-object clusteredBarChart labels
powerbi-report-author formatting describe-property clusteredBarChart labels dynamicLabelDetail
powerbi-report-author formatting describe-object clusteredBarChart dataPoint
powerbi-report-author formatting describe-object pivotTable stylePreset
powerbi-report-author formatting search pivotTable 'total|tooltip'
powerbi-report-author formatting describe-property pivotTable visualTooltip section
powerbi-report-author formatting describe-object slicer general
powerbi-report-author formatting describe-object pivotTable general
```

All catalog/formatting/codec commands used here were read-only and exited successfully. The terminal helper failed to initialize inside the sandbox; approved external read-only commands were used. Web browser fetch failures were checked through official GitHub reads or approved Invoke-WebRequest requests, distinguishing actual 404 from web-tool access failure. No tool install/update was performed.

## Preservation verification

A SHA-256 baseline was recorded for the saved report/model before documentation writing and extended to other inventoried protected project artifacts. After writing this note, all 327 baseline files had identical SHA-256 hashes. No report/model/source mutation command was issued. This note is the only artifact created by this task.
