"""Prepare and validate the Power BI handoff without touching original inputs.

Run: python -m src.dashboard.build_dashboard_data
Recheck saved exports: python -m src.dashboard.build_dashboard_data --validate-only
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from src.analysis.run_analysis import ROOT, check_csv_files, write_csv_files
from .prepare import prepare_tables
from .sources import file_hash, protected_inputs, read_sources
from .validate import validate_tables

OUTPUT = ROOT / 'data/dashboard'


def table_contract(rows):
    columns = []
    for field in rows[0]:
        values = [row[field] for row in rows]
        nonnull = next((value for value in values if value is not None), None)
        data_type = 'Date' if field.endswith('_date') else 'Whole number' if type(nonnull) is int else 'Text'
        columns.append({'name': field, 'powerbi_type': data_type, 'nullable': any(v is None for v in values)})
    return columns


def write_validation(evidence):
    totals = evidence['control_totals']
    lines = ['# Dashboard Data Validation', '', f"Run (UTC): {evidence['validated_at_utc']}.", '',
             f"**PASS: {len(evidence['checks'])} source/projection/reconciliation checks and nine exact CSV readbacks; zero failures.**", '',
             '## Method and unchanged definitions', '',
             'The builder reads all nine prior analytics CSVs, compares every field against the previously '
             'validated JSON results, and verifies source/query/export hashes and prior check outcomes. '
             'It also reads the validated aggregate results that were intentionally retained only in '
             'customer_analysis_validation.json: Pareto points, interval distributions, category transitions '
             'and category mixes. No SQLite connection, source query or business eligibility change is needed.', '',
             'The separate validator imports no dashboard preparation functions. It checks projected '
             'values/types/NULLs against original analytical evidence, aggregate grain uniqueness, exact '
             'monetary/count rollups, fixed share denominators, all Pareto points, conditional interval '
             'denominators and every cohort cell. Source and export ratios retain exact integer components. '
             'CSV blank means SQL/analytical NULL, never an invented numeric zero.', '',
             'Category rows have three separate scopes: All completed, One-time, Repeat. All completed '
             'duplicates the combined group sales and must never be summed with group rows. Category '
             'customer/order counts overlap across categories. Segment customers/orders/sales are additive '
             'because the four segments are mutually exclusive. Monthly distinct customers are not additive. '
             'Concentration points are cumulative and not additive. Cohort size is repeated across offsets '
             'and must be summed at M0 only; each rate keeps its original cohort denominator.', '',
             'The monthly display series suppresses gaps and post-completed-window unresolved outcomes '
             'with NULL; original observed item_sales_hundredths and flags remain unchanged. This is a '
             'separate chart field, not a revised KPI. Boundary observed sales remain visible with warnings. '
             'All monetary totals and rational components import as Whole number. Decimal ratios in DAX '
             'are display calculations; the validated six-place KPI text remains Text.', '',
             '## Reconciled totals', '',
             f"- Completed orders: {totals['completed_orders']:,}; persistent completed customers: {totals['customers']:,}.",
             f"- Delivered item sales: {totals['item_sales_hundredths']:,} hundredths; repeat customers: {totals['repeat_customers']:,}.",
             f"- All-status orders: {totals['all_orders']:,}. Delivered rate denominator remains all-status orders.",
             '- Four segment totals and M0 cohort sizes reproduce the completed-customer population.',
             f"- First-to-second category pairs: {totals['repeat_customers']:,}; first-to-second timing bins: {totals['repeat_customers']:,}; "
             f"all consecutive timing bins: {totals['consecutive_intervals']:,}.", '',
             '## Files, row counts and grains', '']
    for name, detail in evidence['tables'].items():
        lines.append(f"- data/dashboard/{name}.csv: {detail['rows']:,} rows; key/grain: {', '.join(detail['grain'])}.")
    lines.extend(['', 'dashboard_manifest.json records exact headers, Power BI types, NULL support, grains, '
                  'input hashes and export hashes. No customer/order/product/seller identifiers are exported.', '',
                  '## Check outcomes', ''])
    lines.extend(f"- PASS: {check['name']}." for check in evidence['checks'])
    lines.extend(['- PASS: nine saved CSVs reread field by field, preserving headers, row order, exact integers and blanks.',
                  f"- PASS: all {len(evidence['protected_hashes'])} protected inputs retain identical before/after SHA-256 hashes.", '',
                  '## Reproduction', '', '```powershell', '.\\.venv\\Scripts\\python.exe -m src.dashboard.build_dashboard_data',
                  '.\\.venv\\Scripts\\python.exe -m src.dashboard.build_dashboard_data --validate-only', '```', '',
                  'Files are staged/read back before individual replacement; the manifest is published last. '
                  'This is not one multi-file filesystem transaction. Run one instance at a time and '
                  'use --validate-only after an interrupted run. All prior raw/processed/database/schema '
                  'files, analytical exports and validation evidence remain unchanged.', '',
                  '## Power BI acceptance boundary', '',
                  '**The CSV analytical handoff is reconciled to the validated prior layers.** The '
                  'specification, import function and DAX measure definitions are provided for Desktop '
                  'assembly. No PBIX was created, and DAX/visual interactions/conditional formatting have '
                  'not been executed in the Power BI engine. The specification includes acceptance '
                  'checks for types, exact card values, filter scope, zero versus NULL rendering and '
                  'missing/untranslated categories. Complete these before publishing the report.', ''])
    (ROOT / 'reports/dashboard_data_validation.md').write_text('\n'.join(lines), encoding='utf-8')
    (ROOT / 'reports/dashboard_data_validation.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


def main(validate_only=False):
    before = protected_inputs()
    business, customer, source_checks = read_sources()
    tables = prepare_tables(business, customer)
    evidence = validate_tables(tables, business, customer)
    evidence['checks'] = source_checks + evidence['checks']
    if before != protected_inputs():
        raise ValueError('A protected source/database/schema/analytical file changed')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    details = {name: {'rows': len(rows), 'grain': list(evidence['grains'][name]), 'columns': table_contract(rows)}
               for name, rows in tables.items()}
    if validate_only:
        check_csv_files(OUTPUT, tables)
    else:
        with tempfile.TemporaryDirectory(prefix='dashboard_', dir=OUTPUT) as temporary:
            folder = Path(temporary)
            write_csv_files(folder, tables)
            check_csv_files(folder, tables)
            for name in tables:
                os.replace(folder / f'{name}.csv', OUTPUT / f'{name}.csv')
    for name in details:
        details[name]['sha256'] = file_hash(OUTPUT / f'{name}.csv')
    manifest = {'format_version': 1, 'scope': 'Historical validated aggregates; disconnected Power BI tables',
                'null_policy': 'blank CSV fields are NULL; preserve blanks', 'monetary_scale': 'integer hundredths; currency unspecified',
                'tables': details, 'source_hashes': before}
    manifest_path = OUTPUT / 'dashboard_manifest.json'
    if validate_only:
        if json.loads(manifest_path.read_text(encoding='utf-8')) != manifest:
            raise ValueError('Dashboard manifest differs from validated export contract')
    else:
        temporary_manifest = OUTPUT / 'dashboard_manifest.tmp'
        temporary_manifest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary_manifest, manifest_path)
    if before != protected_inputs():
        raise ValueError('Protected files changed during publication')
    evidence.update({'validated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                     'tables': details, 'protected_hashes': before, 'manifest_sha256': file_hash(manifest_path)})
    write_validation(evidence)
    print(f"PASS: {len(evidence['checks'])} checks and nine CSV readbacks; {len(tables)} dashboard datasets.")
    for name, detail in details.items():
        print(f"{name}.csv: {detail['rows']} aggregate rows")
    print('Protected database/schema/source/prior analytical files unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    main(parser.parse_args().validate_only)
