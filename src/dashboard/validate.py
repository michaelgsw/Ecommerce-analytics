"""Reconcile every dashboard field and derived display rule to prior evidence.

Expected projections are built here without importing the dashboard preparer.
Aggregate checks use integer arithmetic. Reports contain no source identifiers.
"""

from datetime import date

from src.analysis.validate_metrics import record_check


def validate_tables(tables, business, customer):
    evidence = {'checks': []}

    def check(name, expected, observed):
        record_check(evidence, name, expected, observed)

    def projection(name, source_rows, mapping, extra=None):
        expected = []
        for source in source_rows:
            row = {target: source[field] for target, field in mapping.items()}
            if extra:
                row.update(extra(source))
            expected.append(row)
        check(f'{name}: every projected value/type/NULL', expected, tables[name])

    def copied(name, sources, omitted=(), extras=None):
        fields = [field for field in tables[name][0] if field not in omitted]
        projection(name, sources, {field: field for field in fields}, extras)

    sales, overview, status = business['sales_overview'][0], business['customer_overview'][0], business['order_status_summary'][0]
    total_customers, total_sales, total_orders = overview['unique_customers'], sales['item_sales_hundredths'], sales['completed_orders']
    kpis = {row['metric_key']: row for row in tables['dashboard_kpis']}
    check('Seven unique KPI keys', 7, len(kpis))
    expected_kpis = {
        'completed_orders': (total_orders, 1, 'delivered', 'orders'),
        'unique_completed_customers': (total_customers, 1, 'delivered', 'customers'),
        'observed_item_sales': (total_sales, 1, 'delivered', 'hundredths'),
        'average_order_value': (sales['average_order_value_hundredths_numerator'], sales['average_order_value_hundredths_denominator'], 'delivered', 'hundredths'),
        'repeat_customer_rate': (overview['repeat_customer_rate_percent_numerator'], overview['repeat_customer_rate_percent_denominator'], 'delivered', 'percent'),
        'delivered_order_rate': (status['delivered_order_rate_percent_numerator'], status['delivered_order_rate_percent_denominator'], 'all_orders', 'percent'),
        'all_orders': (status['status_share_percent_denominator'], 1, 'all_orders', 'orders')}
    check('All KPI rational components/populations/units', expected_kpis,
          {key: (row['numerator'], row['denominator'], row['population'], row['unit']) for key, row in kpis.items()})
    expected_displays = {
        'completed_orders': str(total_orders), 'unique_completed_customers': str(total_customers),
        'observed_item_sales': str(total_sales), 'all_orders': str(status['status_share_percent_denominator']),
        'average_order_value': sales['average_order_value_hundredths'], 'repeat_customer_rate': overview['repeat_customer_rate_percent'],
        'delivered_order_rate': status['delivered_order_rate_percent']}
    check('KPI display text equals prior validated values', expected_displays, {key: row['display_value_text'] for key, row in kpis.items()})
    check('Unambiguous KPI labels', {
        'completed_orders': 'Completed orders', 'unique_completed_customers': 'Unique completed customers',
        'observed_item_sales': 'Observed item sales', 'average_order_value': 'Average order value',
        'repeat_customer_rate': 'Observed repeat customer rate', 'delivered_order_rate': 'Delivered order rate',
        'all_orders': 'All observed orders'}, {key: row['metric_label'] for key, row in kpis.items()})
    check('KPI population-specific period labels; no completed date assigned to operations',
          {key: (sales['first_completed_purchase_timestamp'][:10], sales['last_completed_purchase_timestamp'][:10],
                 sales['first_completed_purchase_timestamp'][:7], sales['last_completed_purchase_timestamp'][:7]) if source[2] == 'delivered'
                else (None, None, business['monthly_sales'][0]['month'], business['monthly_sales'][-1]['month']) for key, source in expected_kpis.items()},
          {key: (r['completed_window_start_date'], r['completed_window_end_date'], r['metric_window_start_month'], r['metric_window_end_month']) for key, r in kpis.items()})
    latest_month = sales['last_completed_purchase_timestamp'][:7]

    def month_extra(source):
        status = 'calendar_gap' if source['all_orders'] == 0 else 'completed_outcome_unobserved' if source['month'] > latest_month else 'boundary_observed' if source['flag_extract_boundary_month'] or source['flag_completed_sales_boundary_month'] else 'interior_observed'
        return {'month_date': source['month'] + '-01', 'coverage_status': status,
                'chart_item_sales_hundredths': source['item_sales_hundredths'] if status in ('interior_observed', 'boundary_observed') else None}
    copied('dashboard_monthly_sales', business['monthly_sales'], ('month_date', 'coverage_status', 'chart_item_sales_hundredths'), month_extra)
    check('Monthly sales/orders exactly additive; distinct monthly customers not summed', (total_sales, total_orders),
          (sum(r['item_sales_hundredths'] for r in tables['dashboard_monthly_sales']), sum(r['completed_orders'] for r in tables['dashboard_monthly_sales'])))
    copied('dashboard_customer_segments', customer['customer_segments'], ('customer_type', 'highlight_high_value_one_time'),
           lambda r: {'customer_type': r['frequency_group'], 'highlight_high_value_one_time': int(r['segment'] == 'High-value one-time')})
    segments = tables['dashboard_customer_segments']
    check('Segment customer/order/sales totals', (total_customers, total_orders, total_sales),
          tuple(sum(r[field] for r in segments) for field in ('customers', 'completed_orders', 'item_sales_hundredths')))
    for source in customer['purchase_group_comparison']:
        scoped = [r for r in segments if r['customer_type'] == source['frequency_group']]
        check(f"{source['frequency_group']}: weighted means retain original denominators",
              (source['customers'], source['completed_orders'], source['item_sales_hundredths']),
              tuple(sum(r[field] for r in scoped) for field in ('customers', 'completed_orders', 'item_sales_hundredths')))
    curve = tables['dashboard_customer_concentration']
    points = [r for r in curve if r['record_type'] == 'pareto_point']
    copied_fields = ('target_customer_percent', 'customers_selected', 'item_sales_hundredths', 'actual_customer_percent_numerator',
                     'actual_customer_percent_denominator', 'cumulative_sales_percent_numerator', 'cumulative_sales_percent_denominator', 'cutoff_customer_sales_hundredths')
    check('All 100 cumulative Pareto points exactly preserved',
          [{field: r[field] for field in copied_fields} for r in customer['pareto_concentration']],
          [{field: r[field] for field in copied_fields} for r in points])
    check('Pareto monotonic endpoints', (100, total_customers, total_sales, True),
          (len(points), points[-1]['customers_selected'], points[-1]['item_sales_hundredths'],
           all(a['item_sales_hundredths'] <= b['item_sales_hundredths'] for a, b in zip(points, points[1:]))))
    check('Top 1/5/10/20 highlight labels', [1, 5, 10, 20], [r['target_customer_percent'] for r in points if r['highlight_top_group']])
    inverse = customer['customers_for_80_percent_sales'][0]
    expected_inverse = {'record_type': 'sales_80_threshold', 'target_customer_percent': None,
                        'customers_selected': inverse['customers_selected'], 'item_sales_hundredths': inverse['item_sales_hundredths'],
                        'actual_customer_percent_numerator': inverse['customer_share_percent_numerator'],
                        'actual_customer_percent_denominator': inverse['customer_share_percent_denominator'],
                        'cumulative_sales_percent_numerator': inverse['sales_share_percent_numerator'],
                        'cumulative_sales_percent_denominator': inverse['sales_share_percent_denominator'],
                        'cutoff_customer_sales_hundredths': None, 'target_sales_percent': 80, 'highlight_top_group': 0}
    check('Actual 80% threshold exactly retained', [expected_inverse], [r for r in curve if r['record_type'] == 'sales_80_threshold'])
    summaries = {r['cohort_month']: r for r in customer['customer_cohort_summary']}
    flags = ('flag_insufficient_three_month_coverage', 'flag_initial_boundary_cohort', 'flag_terminal_boundary_cohort')
    copied('dashboard_cohorts', customer['cohort_retention_long'], ('cohort_date', *flags),
           lambda r: {'cohort_date': r['cohort_month'] + '-01', **{f: summaries[r['cohort_month']][f] for f in flags}})
    cells = tables['dashboard_cohorts']
    check('Only M0 cohort sizes are additive', total_customers, sum(r['new_customers'] for r in cells if r['month_index'] == 0))
    check('Every cohort-cell denominator equals its original cohort size', 0,
          sum(r['retention_percent_denominator'] != summaries[r['cohort_month']]['new_customers'] for r in cells))
    check('Unavailable cohort rates/counts stay NULL', 0,
          sum(r['returning_customers_for_rate'] is not None or r['retention_percent_numerator'] is not None
              for r in cells if r['coverage_status'] not in ('interior_observed', 'baseline_membership')))
    check('Future observed counts stay NULL', 0, sum(r['observed_customers'] is not None for r in cells if r['coverage_status'] == 'future_unobserved'))
    common = {r['cohort_month'] for r in customer['customer_cohort_summary'] if not r['flag_insufficient_three_month_coverage']}
    for month in (1, 2, 3):
        expected = (sum(r[f'customers_returning_month_{month}'] for r in customer['customer_cohort_summary'] if r['cohort_month'] in common),
                    sum(r['new_customers'] for r in customer['customer_cohort_summary'] if r['cohort_month'] in common))
        scoped = [r for r in cells if r['month_index'] == month and r['flag_insufficient_three_month_coverage'] == 0]
        check(f'M{month}: common-cohort card returns and original-size denominator', expected,
              (sum(r['returning_customers_for_rate'] for r in scoped), sum(r['retention_percent_denominator'] for r in scoped)))
    timing = tables['dashboard_repeat_timing']
    summaries = [r for r in timing if r['record_type'] == 'summary']
    check('All nine timing metrics retain exact counts and rational pairs',
          [(r['metric'], r['count'], r['value_numerator'], r['value_denominator']) for r in customer['repeat_purchase_summary']],
          [(r['metric'], r['count'], r['numerator'], r['denominator']) for r in summaries])
    windows = {'within_30_days': 30, 'within_60_days': 60, 'within_90_days': 90, 'within_180_days': 180}
    check('Timing summary units, scope and window ordering',
          [('all_consecutive' if r['metric'] == 'all_consecutive_repeat_intervals' else 'first_to_second',
            'days' if r['metric'] == 'median_days_to_second_purchase' else 'percent' if r['value_denominator'] else 'count',
            windows.get(r['metric'], 0)) for r in customer['repeat_purchase_summary']],
          [(r['scope'], r['unit'], r['sort_order']) for r in summaries])
    intervals = [r for r in timing if r['record_type'] == 'interval_bin']
    check('All fourteen interval bins retain scope/count/range',
          [(r['scope'], r['interval_bin'], r['intervals'], r['min_days'], r['max_days']) for r in customer['repeat_interval_distribution']],
          [(r['scope'], r['metric'], r['count'], r['min_days'], r['max_days']) for r in intervals])
    totals = {r['metric']: r['count'] for r in customer['repeat_purchase_summary']}
    for scope, denominator in (('first_to_second', totals['repeat_customers']), ('all_consecutive', totals['all_consecutive_repeat_intervals'])):
        scoped = [r for r in intervals if r['scope'] == scope]
        check(f'{scope}: mutually exclusive timing bins and conditional denominators', (denominator, 0),
              (sum(r['count'] for r in scoped), sum(r['numerator'] != 100 * r['count'] or r['denominator'] != denominator for r in scoped)))
    expected_categories = []
    for group, sources in [('All completed', business['category_performance']), ('customer_group', customer['category_customer_behavior'])]:
        for source in sources:
            label = source['product_category_name']
            expected_categories.append({'customer_type': group if group != 'customer_group' else source['frequency_group'],
                'product_category_name': label, 'product_category_name_english': source['product_category_name_english'],
                'category_key': 'missing:' if label is None else 'source:' + label,
                'category_display': '[Missing source category]' if label is None else label,
                'flag_category_missing': int(label is None), 'flag_translation_missing': int(label is not None and source['product_category_name_english'] is None),
                'item_sales_hundredths': source['item_sales_hundredths'], 'category_orders': source['completed_orders'],
                'items_sold': source['items_sold'] if group == 'All completed' else source['items_purchased'],
                'category_customers': None if group == 'All completed' else source['customers'], 'sales_rank': source['sales_rank'],
                'sales_share_percent_numerator': source['sales_share_percent_numerator'] if group == 'All completed' else source['group_sales_share_percent_numerator'],
                'sales_share_percent_denominator': source['sales_share_percent_denominator'] if group == 'All completed' else source['group_sales_share_percent_denominator']})
    categories = tables['dashboard_categories']
    check('Every category scope/key/value/rank/NULL/translation flag', expected_categories, categories)
    for group, expected_sales in [('All completed', total_sales), *[(r['frequency_group'], r['item_sales_hundredths']) for r in customer['purchase_group_comparison']]]:
        scoped = [r for r in categories if r['customer_type'] == group]
        check(f'{group}: category sales additive with fixed full-group denominator', (expected_sales, {expected_sales}),
              (sum(r['item_sales_hundredths'] for r in scoped), {r['sales_share_percent_denominator'] for r in scoped}))
    transitions = tables['dashboard_category_transition']
    copied('dashboard_category_transition', [r for r in customer['category_transitions'] if r['scope'] == 'first_to_second'], ('behavior_display', 'sort_order'),
           lambda r: {'behavior_display': {'same_category_set': 'Same category set', 'overlap_with_change': 'Overlapping changed set', 'no_category_overlap': 'No overlap', 'category_unknown': 'Unknown category'}[r['behavior']],
                      'sort_order': {'same_category_set': 1, 'overlap_with_change': 2, 'no_category_overlap': 3, 'category_unknown': 4}[r['behavior']]})
    check('Category transitions: one pair per observed repeat customer', totals['repeat_customers'], sum(r['order_transitions'] for r in transitions))
    copied('dashboard_order_status', business['order_status_summary'])
    check('Status counts cover all orders', status['status_share_percent_denominator'], sum(r['orders'] for r in tables['dashboard_order_status']))
    keys = {'dashboard_kpis': ('metric_key',), 'dashboard_monthly_sales': ('month',), 'dashboard_customer_segments': ('segment',),
            'dashboard_customer_concentration': ('record_type', 'target_customer_percent'), 'dashboard_cohorts': ('cohort_month', 'month_index'),
            'dashboard_repeat_timing': ('record_type', 'scope', 'metric'), 'dashboard_categories': ('customer_type', 'category_key'),
            'dashboard_category_transition': ('behavior',), 'dashboard_order_status': ('order_status',)}
    for name, rows in tables.items():
        check(f'{name}: unique documented aggregate grain', len(rows), len({tuple(r[k] for k in keys[name]) for r in rows}))
        if any(field in ('customer_id', 'customer_unique_id', 'order_id', 'product_id', 'seller_id') for field in rows[0]):
            raise ValueError(f'{name}: forbidden identifier export')
        for row in rows:
            for field, value in row.items():
                if value is not None and type(value) not in (str, int):
                    raise ValueError(f'{name}.{field}: noninteger/text analytical storage')
                if field.endswith('_date') and value is not None:
                    date.fromisoformat(value)
    failures = [r['name'] for r in evidence['checks'] if not r['passed']]
    if failures:
        raise ValueError('Dashboard reconciliation failed: ' + '; '.join(failures))
    # Keep validation JSON compact: full datasets already live in validated CSVs.
    evidence['checks'] = [{'name': r['name'], 'passed': r['passed']} for r in evidence['checks']]
    evidence['grains'] = keys
    evidence['control_totals'] = {'customers': total_customers, 'completed_orders': total_orders, 'item_sales_hundredths': total_sales,
                                 'all_orders': status['status_share_percent_denominator'], 'repeat_customers': totals['repeat_customers'],
                                 'consecutive_intervals': totals['all_consecutive_repeat_intervals']}
    return evidence
