"""Read validated evidence/CSVs and protect the completed project inputs."""

import csv
import hashlib
import json

from src.analysis.run_analysis import ROOT, protected_hashes


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protected_inputs():
    hashes = protected_hashes()
    for folder, pattern in (('data/analytics', '*.csv'), ('reports', '*validation.json')):
        for path in sorted((ROOT / folder).glob(pattern)):
            if path.name == 'dashboard_data_validation.json':
                continue
            hashes[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for relative in ('reports/business_metric_validation.md', 'reports/customer_analysis_findings.md',
                     'reports/customer_analysis_validation.md', 'docs/kpi_definitions.md'):
        hashes[relative] = file_hash(ROOT / relative)
    return hashes


def csv_strings(rows):
    return [{key: '' if value is None else str(value) for key, value in row.items()} for row in rows]


def read_sources():
    reports = {}
    csv_checks = []
    for name in ('business_metric_validation', 'customer_analysis_validation'):
        report = json.loads((ROOT / 'reports' / f'{name}.json').read_text(encoding='utf-8'))
        if not report['checks'] or not all(check['passed'] for check in report['checks']):
            raise ValueError(f'{name}: prior validation contains failures')
        for relative, expected in report['protected_hashes'].items():
            if file_hash(ROOT / relative) != expected:
                raise ValueError(f'{name}: protected input changed: {relative}')
        for filename, expected in report['query_hashes'].items():
            query = (ROOT / 'sql/analysis' / filename).read_text(encoding='utf-8')
            if hashlib.sha256(query.encode('utf-8')).hexdigest() != expected:
                raise ValueError(f'{name}: analytical query changed: {filename}')
        for filename, expected in report['export_hashes'].items():
            path = ROOT / 'data/analytics' / filename
            if file_hash(path) != expected:
                raise ValueError(f'{name}: analytical CSV changed: {filename}')
            with path.open(encoding='utf-8', newline='') as stream:
                rows = list(csv.DictReader(stream))
            key = path.stem
            if key == 'cohort_retention_matrix':
                # Read the wide export against the validated long evidence, cell by cell.
                expected_rows = {}
                for cell in report['results']['cohort_retention_long']:
                    row = expected_rows.setdefault(cell['cohort_month'], {
                        'cohort_month': cell['cohort_month'], 'new_customers': cell['new_customers']})
                    prefix = f"month_{cell['month_index']}"
                    row[prefix + '_observed_customers'] = cell['observed_customers']
                    row[prefix + '_returning_customers'] = cell['returning_customers_for_rate']
                    row[prefix + '_retention_percent'] = cell['retention_percent']
                    row[prefix + '_coverage'] = cell['coverage_status']
                expected_rows = list(expected_rows.values())
            else:
                expected_rows = report['results'][key]
            if rows != csv_strings(expected_rows):
                raise ValueError(f'{filename}: field-level evidence reconciliation failed')
            csv_checks.append({'name': f'Prior CSV/evidence/hash: {filename}', 'passed': True, 'rows': len(rows)})
        reports[name] = report
    database = json.loads((ROOT / 'reports/database_validation.json').read_text(encoding='utf-8'))
    if file_hash(ROOT / 'data/database/olist_analytics.db') != database['database_sha256']:
        raise ValueError('Database differs from independent validation evidence')
    return reports['business_metric_validation']['results'], reports['customer_analysis_validation']['results'], csv_checks
