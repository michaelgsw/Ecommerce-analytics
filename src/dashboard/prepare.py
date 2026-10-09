"""Project validated aggregates into nine compact dashboard tables.

No source query, KPI eligibility, threshold, or original numerator is changed.
No customer/order identifiers or database connections are needed.
"""

from src.analysis.run_analysis import decimal_ratio


def select(row, fields):
    return {field: row[field] for field in fields}


def kpis(business):
    sales = business['sales_overview'][0]
    customer = business['customer_overview'][0]
    status = business['order_status_summary'][0]
    definitions = (
        ('completed_orders', 'Completed orders', 'delivered', 'orders', sales['completed_orders'], 1),
        ('unique_completed_customers', 'Unique completed customers', 'delivered', 'customers', customer['unique_customers'], 1),
        ('observed_item_sales', 'Observed item sales', 'delivered', 'hundredths', sales['item_sales_hundredths'], 1),
        ('average_order_value', 'Average order value', 'delivered', 'hundredths', sales['average_order_value_hundredths_numerator'], sales['average_order_value_hundredths_denominator']),
        ('repeat_customer_rate', 'Observed repeat customer rate', 'delivered', 'percent', customer['repeat_customer_rate_percent_numerator'], customer['repeat_customer_rate_percent_denominator']),
        ('delivered_order_rate', 'Delivered order rate', 'all_orders', 'percent', status['delivered_order_rate_percent_numerator'], status['delivered_order_rate_percent_denominator']),
        ('all_orders', 'All observed orders', 'all_orders', 'orders', status['status_share_percent_denominator'], 1),
    )
    return [{'metric_key': key, 'metric_label': label, 'population': population, 'unit': unit,
             'numerator': numerator, 'denominator': denominator,
             'display_value_text': str(numerator) if denominator == 1 else decimal_ratio(numerator, denominator),
             'completed_window_start_date': sales['first_completed_purchase_timestamp'][:10] if population == 'delivered' else None,
             'completed_window_end_date': sales['last_completed_purchase_timestamp'][:10] if population == 'delivered' else None,
             'metric_window_start_month': sales['first_completed_purchase_timestamp'][:7] if population == 'delivered' else business['monthly_sales'][0]['month'],
             'metric_window_end_month': sales['last_completed_purchase_timestamp'][:7] if population == 'delivered' else business['monthly_sales'][-1]['month']}
            for key, label, population, unit, numerator, denominator in definitions]


def monthly(business):
    last_completed = business['sales_overview'][0]['last_completed_purchase_timestamp'][:7]
    fields = ('month', 'all_orders', 'completed_orders', 'distinct_customers', 'item_sales_hundredths',
              'average_order_value_hundredths_numerator', 'average_order_value_hundredths_denominator',
              'flag_extract_boundary_month', 'flag_completed_sales_boundary_month', 'flag_no_observed_orders',
              'flag_mom_comparable', 'item_sales_mom_percent_numerator', 'item_sales_mom_percent_denominator')
    rows = []
    for source in business['monthly_sales']:
        row = select(source, fields)
        row['month_date'] = source['month'] + '-01'
        if source['flag_no_observed_orders']:
            coverage = 'calendar_gap'
        elif source['month'] > last_completed:
            coverage = 'completed_outcome_unobserved'
        elif source['flag_extract_boundary_month'] or source['flag_completed_sales_boundary_month']:
            coverage = 'boundary_observed'
        else:
            coverage = 'interior_observed'
        row['coverage_status'] = coverage
        # Display-only gap protection. The original observed KPI total remains above.
        row['chart_item_sales_hundredths'] = None if coverage in ('calendar_gap', 'completed_outcome_unobserved') else source['item_sales_hundredths']
        rows.append(row)
    return rows


def segments(customer):
    fields = ('segment', 'customers', 'completed_orders', 'item_sales_hundredths', 'freight_hundredths',
              'average_customer_sales_hundredths_numerator', 'average_customer_sales_hundredths_denominator',
              'average_order_value_hundredths_numerator', 'average_order_value_hundredths_denominator',
              'customer_share_percent_numerator', 'customer_share_percent_denominator',
              'sales_share_percent_numerator', 'sales_share_percent_denominator',
              'high_value_threshold_hundredths_numerator', 'high_value_threshold_hundredths_denominator', 'observation_date')
    return [{**select(source, fields), 'customer_type': source['frequency_group'],
             'highlight_high_value_one_time': int(source['segment'] == 'High-value one-time')}
            for source in customer['customer_segments']]


def concentration(customer):
    rows = []
    for source in customer['pareto_concentration']:
        row = select(source, ('target_customer_percent', 'customers_selected', 'item_sales_hundredths',
                             'actual_customer_percent_numerator', 'actual_customer_percent_denominator',
                             'cumulative_sales_percent_numerator', 'cumulative_sales_percent_denominator',
                             'cutoff_customer_sales_hundredths'))
        rows.append({'record_type': 'pareto_point', **row, 'target_sales_percent': None,
                     'highlight_top_group': int(source['target_customer_percent'] in (1, 5, 10, 20))})
    source = customer['customers_for_80_percent_sales'][0]
    rows.append({'record_type': 'sales_80_threshold', 'target_customer_percent': None,
                 'customers_selected': source['customers_selected'], 'item_sales_hundredths': source['item_sales_hundredths'],
                 'actual_customer_percent_numerator': source['customer_share_percent_numerator'],
                 'actual_customer_percent_denominator': source['customer_share_percent_denominator'],
                 'cumulative_sales_percent_numerator': source['sales_share_percent_numerator'],
                 'cumulative_sales_percent_denominator': source['sales_share_percent_denominator'],
                 'cutoff_customer_sales_hundredths': None, 'target_sales_percent': 80, 'highlight_top_group': 0})
    return rows


def cohorts(customer):
    summaries = {row['cohort_month']: row for row in customer['customer_cohort_summary']}
    fields = ('cohort_month', 'new_customers', 'month_index', 'target_month', 'coverage_status', 'observed_customers',
              'returning_customers_for_rate', 'retention_percent_numerator', 'retention_percent_denominator')
    flags = ('flag_insufficient_three_month_coverage', 'flag_initial_boundary_cohort', 'flag_terminal_boundary_cohort')
    return [{**select(source, fields), 'cohort_date': source['cohort_month'] + '-01',
             **select(summaries[source['cohort_month']], flags)} for source in customer['cohort_retention_long']]


def repeat_timing(customer):
    window_order = {'within_30_days': 30, 'within_60_days': 60, 'within_90_days': 90, 'within_180_days': 180}
    rows = []
    totals = {row['metric']: row['count'] for row in customer['repeat_purchase_summary']}
    for source in customer['repeat_purchase_summary']:
        key = source['metric']
        unit = 'days' if key == 'median_days_to_second_purchase' else 'percent' if source['value_denominator'] else 'count'
        rows.append({'record_type': 'summary', 'scope': 'all_consecutive' if key == 'all_consecutive_repeat_intervals' else 'first_to_second',
                     'metric': key, 'sort_order': window_order.get(key, 0), 'count': source['count'],
                     'numerator': source['value_numerator'], 'denominator': source['value_denominator'],
                     'unit': unit, 'min_days': None, 'max_days': None})
    for source in customer['repeat_interval_distribution']:
        denominator = totals['repeat_customers'] if source['scope'] == 'first_to_second' else totals['all_consecutive_repeat_intervals']
        rows.append({'record_type': 'interval_bin', 'scope': source['scope'], 'metric': source['interval_bin'],
                     'sort_order': int(source['interval_bin'][:2]), 'count': source['intervals'],
                     'numerator': 100 * source['intervals'], 'denominator': denominator, 'unit': 'percent',
                     'min_days': source['min_days'], 'max_days': source['max_days']})
    return rows


def category_identity(source):
    label, english = source['product_category_name'], source['product_category_name_english']
    return {'product_category_name': label, 'product_category_name_english': english,
            'category_key': 'missing:' if label is None else 'source:' + label,
            'category_display': '[Missing source category]' if label is None else label,
            'flag_category_missing': int(label is None),
            'flag_translation_missing': int(label is not None and english is None)}


def categories(business, customer):
    rows = []
    for source in business['category_performance']:
        rows.append({'customer_type': 'All completed', **category_identity(source),
                     'item_sales_hundredths': source['item_sales_hundredths'], 'category_orders': source['completed_orders'],
                     'items_sold': source['items_sold'], 'category_customers': None, 'sales_rank': source['sales_rank'],
                     'sales_share_percent_numerator': source['sales_share_percent_numerator'],
                     'sales_share_percent_denominator': source['sales_share_percent_denominator']})
    for source in customer['category_customer_behavior']:
        rows.append({'customer_type': source['frequency_group'], **category_identity(source),
                     'item_sales_hundredths': source['item_sales_hundredths'], 'category_orders': source['completed_orders'],
                     'items_sold': source['items_purchased'], 'category_customers': source['customers'], 'sales_rank': source['sales_rank'],
                     'sales_share_percent_numerator': source['group_sales_share_percent_numerator'],
                     'sales_share_percent_denominator': source['group_sales_share_percent_denominator']})
    return rows


def transitions(customer):
    labels = {'same_category_set': 'Same category set', 'overlap_with_change': 'Overlapping changed set',
              'no_category_overlap': 'No overlap', 'category_unknown': 'Unknown category'}
    order = {'same_category_set': 1, 'overlap_with_change': 2, 'no_category_overlap': 3, 'category_unknown': 4}
    return [{**select(source, ('scope', 'behavior', 'order_transitions', 'distinct_customers', 'tied_timestamp_transitions',
                              'transition_share_percent_numerator', 'transition_share_percent_denominator')),
             'behavior_display': labels[source['behavior']], 'sort_order': order[source['behavior']]}
            for source in customer['category_transitions'] if source['scope'] == 'first_to_second']


def order_status(business):
    return [select(source, ('order_status', 'orders', 'status_share_percent_numerator', 'status_share_percent_denominator',
                           'orders_missing_items', 'orders_missing_payments', 'orders_missing_reviews'))
            for source in business['order_status_summary']]


def prepare_tables(business, customer):
    return {'dashboard_kpis': kpis(business), 'dashboard_monthly_sales': monthly(business),
            'dashboard_customer_segments': segments(customer), 'dashboard_customer_concentration': concentration(customer),
            'dashboard_cohorts': cohorts(customer), 'dashboard_repeat_timing': repeat_timing(customer),
            'dashboard_categories': categories(business, customer), 'dashboard_category_transition': transitions(customer),
            'dashboard_order_status': order_status(business)}
