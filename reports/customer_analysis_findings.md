# Customer Analysis Findings

Validated (UTC): 2026-10-06T01:28:22+00:00. Eligible population: 93,358 persistent customers, 96,478 delivered orders, 1,322,149,811 item-sales hundredths.

Money is expressed in exact hundredths without a currency assertion. Displayed ratios are Decimal values rounded to six places; their exact integer components remain in the CSV/JSON evidence. All findings describe the available historical extract.

## Purchase frequency and customer value

- Exact metric: 2,801/93,358 customers repeat (3.000278%); repeat sales are 72,840,875/1,322,149,811 hundredths (5.509275%).
- Comparison: One-time customers: 90,557; mean customer sales 13795.829544 hundredths versus 26005.310603 for repeat customers. AOV: 13795.829544 versus 12302.123797 hundredths. Frequency distribution: 1 order(s): 90,557 customers; 2 order(s): 2,573 customers; 3 order(s): 181 customers; 4 order(s): 28 customers; 5 order(s): 9 customers; 6 order(s): 5 customers; 7 order(s): 3 customers; 9 order(s): 1 customers; 15 order(s): 1 customers.
- Interpretation: The population has very little observed frequency variation. Repeat customers contribute more total observed sales per customer; this includes their additional orders.
- Limitation: These are observed purchases, not lifetime behavior or causal effects of repeating. Later acquisitions have less follow-up; same-day orders can include split/batched transactions.

## Actual customer sales concentration

- Exact metric: Top 1% (934 customers): 151,593,284 hundredths, 11.465666% of sales; Top 5% (4,668 customers): 385,139,214 hundredths, 29.129771% of sales; Top 10% (9,336 customers): 543,402,458 hundredths, 41.099916% of sales; Top 20% (18,672 customers): 748,623,706 hundredths, 56.621700% of sales.
- Comparison: Reaching at least 80% requires 42,009 customers (44.997751%), contributing 1,057,722,676 hundredths (80.000214%). Top 20% falls below 80%.
- Interpretation: Sales are concentrated, but the observed data does not follow an 80/20 split. All 100 cumulative percentile points are retained in the JSON evidence.
- Limitation: Top groups use ceil(N*p/100); exact-N boundary ties are ordered deterministically by persistent ID, without exporting IDs. These groups measure observed item sales, not profit, net revenue, payment receipts or lifetime value.

## Statistically supported descriptive segments

- Exact metric: Q1=4,765, median=8,970, Q3=15,475, P90=27,999, P95=41,986, P99=100,499 hundredths. High value means item sales strictly above Q3+1.5*(Q3-Q1) = 31540.000000 hundredths.
- Comparison: High-value one-time: 7,095 customers, 7.599777% of customers, 456,987,318 hundredths, 34.563959% of sales; High-value repeat: 669 customers, 0.716596% of customers, 39,693,452 hundredths, 3.002190% of sales; Standard one-time: 83,462 customers, 89.399944% of customers, 792,321,618 hundredths, 59.926766% of sales; Standard repeat: 2,132 customers, 2.283682% of customers, 33,147,423 hundredths, 2.507085% of sales.
- Interpretation: The four groups separate observed purchase multiplicity and the robust upper-value tail. The threshold was chosen after inspecting the skewed distribution. Ties at the threshold remain standard, and ties are never split to force equal segment sizes. This is a useful descriptive distinction for this extract.
- Limitation: The Tukey rule identifies an upper tail; it does not establish natural clusters, future value, loyalty or lifetime value. Segment means are partly defined by the rule, not independent proof of predictive usefulness. Customer tenure and acquisition date differ.

## Historical recency and consistent state

- Exact metric: Reference date: 2018-08-29, the latest observed delivered-order purchase date. Nearest-rank median recency: 218 calendar days. 37 customer states remain NULL.
- Comparison: less recent within observed period: 46,678 customers; recency range 219–713 days; recent within observed period: 46,680 customers; recency range 0–218 days.
- Interpretation: Recent within observed period means recency <= the observed median; less recent means greater than it. State is assigned only when all completed-order-associated customer records have one consistent, nonblank source state.
- Limitation: The reference date is an extract boundary, not a certified business cutoff or today's date. These labels do not describe currently active/churned customers. State is the customer-record location, not verified delivery geography; geolocation is not joined.

## Cohort return activity with explicit observation limits

- Exact metric: 23 cohorts reconcile to 93,358 customers. For the same 17 cohorts with all M1–M3 interior observation, M1: 331/68,618 = 0.482381%; M2: 240/68,618 = 0.349762%; M3: 180/68,618 = 0.262322%.
- Comparison: 6 cohorts lack full first-three-month interior coverage. Matrix statuses across 552 cells: baseline_membership=23; calendar_gap=2; future_unobserved=274; interior_observed=231; terminal_partial=22. 1,168 customers repeat within their acquisition month; monthly return activity measures a different behavior than any observed repeat order.
- Interpretation: Later-month activity is low in the shared observed cohort population. Month-specific rates count returning customers against each original cohort size; they are not cumulative and need not decline monotonically.
- Limitation: First acquisition is first observed, not proven first ever. The initial cohort, November 2016 gap and August 2018 terminal partial month limit interpretation. Future, gap and terminal-partial rates are blank, not zero. Older cohorts' overall repeat rates have longer follow-up. Interior months are descriptive and not certified complete. Small cohorts are unstable: September and December 2016 each contain one observed customer; December's 1/1 M1 rate is 100% and cannot represent typical customer behavior.

Cohort-level comparisons (item sales and means include all observed delivered purchases; M1/M2/M3 primary rates use the conservative coverage rule):

- 2016-09: new=1, repeat=0 (0.000000%), sales=13,497 hundredths, mean=13497.000000 hundredths; M1=0.000000% (interior_observed); M2=NULL (calendar_gap); M3=0.000000% (interior_observed); distinct M4+ returns=0; interior future months=21.
- 2016-10: new=262, repeat=12 (4.580153%), sales=4,177,257 hundredths, mean=15943.729008 hundredths; M1=NULL (calendar_gap); M2=0.000000% (interior_observed); M3=0.000000% (interior_observed); distinct M4+ returns=9; interior future months=20.
- 2016-12: new=1, repeat=1 (100.000000%), sales=2,180 hundredths, mean=2180.000000 hundredths; M1=100.000000% (interior_observed); M2=0.000000% (interior_observed); M3=0.000000% (interior_observed); distinct M4+ returns=0; interior future months=19.
- 2017-01: new=717, repeat=52 (7.252441%), sales=11,459,644 hundredths, mean=15982.767085 hundredths; M1=0.278940% (interior_observed); M2=0.278940% (interior_observed); M3=0.139470% (interior_observed); distinct M4+ returns=24; interior future months=18.
- 2017-02: new=1,628, repeat=66 (4.054054%), sales=23,978,846 hundredths, mean=14729.020885 hundredths; M1=0.184275% (interior_observed); M2=0.307125% (interior_observed); M3=0.122850% (interior_observed); distinct M4+ returns=37; interior future months=17.
- 2017-03: new=2,503, repeat=121 (4.834199%), sales=37,164,515 hundredths, mean=14847.988414 hundredths; M1=0.439473% (interior_observed); M2=0.359569% (interior_observed); M3=0.399521% (interior_observed); distinct M4+ returns=60; interior future months=16.
- 2017-04: new=2,256, repeat=102 (4.521277%), sales=35,149,679 hundredths, mean=15580.531472 hundredths; M1=0.620567% (interior_observed); M2=0.221631% (interior_observed); M3=0.177305% (interior_observed); distinct M4+ returns=51; interior future months=15.
- 2017-05: new=3,451, repeat=182 (5.273834%), sales=50,250,872 hundredths, mean=14561.249493 hundredths; M1=0.463634% (interior_observed); M2=0.463634% (interior_observed); M3=0.289771% (interior_observed); distinct M4+ returns=82; interior future months=14.
- 2017-06: new=3,037, repeat=161 (5.301284%), sales=43,436,818 hundredths, mean=14302.541324 hundredths; M1=0.493908% (interior_observed); M2=0.395127% (interior_observed); M3=0.428054% (interior_observed); distinct M4+ returns=73; interior future months=13.
- 2017-07: new=3,752, repeat=175 (4.664179%), sales=49,073,652 hundredths, mean=13079.331557 hundredths; M1=0.533049% (interior_observed); M2=0.346482% (interior_observed); M3=0.239872% (interior_observed); distinct M4+ returns=72; interior future months=12.
- 2017-08: new=4,057, repeat=191 (4.707912%), sales=56,624,959 hundredths, mean=13957.347547 hundredths; M1=0.690165% (interior_observed); M2=0.345083% (interior_observed); M3=0.271136% (interior_observed); distinct M4+ returns=79; interior future months=11.
- 2017-09: new=4,004, repeat=180 (4.495504%), sales=61,385,699 hundredths, mean=15331.093656 hundredths; M1=0.699301% (interior_observed); M2=0.549451% (interior_observed); M3=0.274725% (interior_observed); distinct M4+ returns=67; interior future months=10.
- 2017-10: new=4,328, repeat=160 (3.696858%), sales=65,205,408 hundredths, mean=15065.944547 hundredths; M1=0.716266% (interior_observed); M2=0.254159% (interior_observed); M3=0.092421% (interior_observed); distinct M4+ returns=59; interior future months=9.
- 2017-11: new=7,060, repeat=223 (3.158640%), sales=99,198,385 hundredths, mean=14050.762748 hundredths; M1=0.566572% (interior_observed); M2=0.368272% (interior_observed); M3=0.169972% (interior_observed); distinct M4+ returns=54; interior future months=8.
- 2017-12: new=5,338, repeat=139 (2.603972%), sales=72,152,322 hundredths, mean=13516.733233 hundredths; M1=0.206070% (interior_observed); M2=0.281004% (interior_observed); M3=0.337205% (interior_observed); distinct M4+ returns=35; interior future months=7.
- 2018-01: new=6,842, repeat=208 (3.040047%), sales=92,164,255 hundredths, mean=13470.367583 hundredths; M1=0.336159% (interior_observed); M2=0.365390% (interior_observed); M3=0.292312% (interior_observed); distinct M4+ returns=42; interior future months=6.
- 2018-02: new=6,288, repeat=236 (3.753181%), sales=82,769,111 hundredths, mean=13163.026559 hundredths; M1=0.349873% (interior_observed); M2=0.397583% (interior_observed); M3=0.302163% (interior_observed); distinct M4+ returns=30; interior future months=5.
- 2018-03: new=6,774, repeat=162 (2.391497%), sales=94,690,105 hundredths, mean=13978.462504 hundredths; M1=0.398583% (interior_observed); M2=0.295247% (interior_observed); M3=0.295247% (interior_observed); distinct M4+ returns=8; interior future months=4.
- 2018-04: new=6,582, repeat=129 (1.959891%), sales=96,222,503 hundredths, mean=14619.037223 hundredths; M1=0.592525% (interior_observed); M2=0.303859% (interior_observed); M3=0.243087% (interior_observed); distinct M4+ returns=NULL; interior future months=3.
- 2018-05: new=6,506, repeat=109 (1.675377%), sales=96,388,408 hundredths, mean=14815.310175 hundredths; M1=0.522595% (interior_observed); M2=0.261297% (interior_observed); M3=NULL (terminal_partial); distinct M4+ returns=NULL; interior future months=2.
- 2018-06: new=5,878, repeat=70 (1.190881%), sales=83,471,045 hundredths, mean=14200.586084 hundredths; M1=0.425315% (interior_observed); M2=NULL (terminal_partial); M3=NULL (future_unobserved); distinct M4+ returns=NULL; interior future months=1.
- 2018-07: new=5,949, repeat=88 (1.479240%), sales=85,164,743 hundredths, mean=14315.808203 hundredths; M1=NULL (terminal_partial); M2=NULL (future_unobserved); M3=NULL (future_unobserved); distinct M4+ returns=NULL; interior future months=0.
- 2018-08: new=6,144, repeat=34 (0.553385%), sales=82,005,908 hundredths, mean=13347.315755 hundredths; M1=NULL (future_unobserved); M2=NULL (future_unobserved); M3=NULL (future_unobserved); distinct M4+ returns=NULL; interior future months=0.

## Conditional repeat-purchase timing

- Exact metric: Median first-to-second interval among 2,801 observed repeat customers: 29.000000 calendar days. Within 30 days: 1,416/2,801 (50.553374%); Within 60 days: 1,712/2,801 (61.121028%); Within 90 days: 1,908/2,801 (68.118529%); Within 180 days: 2,321/2,801 (82.863263%).
- Comparison: Same-day seconds: 829 (29.596573%); identical first/second timestamps: 253. All consecutive intervals: 3,120, versus one first-to-second interval per repeat customer (2,801).
- Interpretation: A substantial share of observed seconds occurs quickly, and same-day purchases materially affect the interval distribution. Detailed mutually exclusive day bins are retained below.
- Limitation: Denominator is only observed repeat customers. These percentages are not probabilities that any customer will repeat within those windows, and do not adjust for censoring. Same-day/tied timestamps cannot establish separate shopping intent. Deterministic ID ordering resolves ties computationally, not their true purchase sequence.

Interval distributions (calendar days; each interval belongs to one bin):

- all_consecutive / 01_same_day: 890 intervals, observed range 0–0 days.
- all_consecutive / 02_1_to_30_days: 678 intervals, observed range 1–30 days.
- all_consecutive / 03_31_to_60_days: 360 intervals, observed range 31–60 days.
- all_consecutive / 04_61_to_90_days: 221 intervals, observed range 61–90 days.
- all_consecutive / 05_91_to_180_days: 462 intervals, observed range 91–180 days.
- all_consecutive / 06_181_to_365_days: 425 intervals, observed range 181–365 days.
- all_consecutive / 07_over_365_days: 84 intervals, observed range 366–609 days.
- first_to_second / 01_same_day: 829 intervals, observed range 0–0 days.
- first_to_second / 02_1_to_30_days: 587 intervals, observed range 1–30 days.
- first_to_second / 03_31_to_60_days: 296 intervals, observed range 31–60 days.
- first_to_second / 04_61_to_90_days: 196 intervals, observed range 61–90 days.
- first_to_second / 05_91_to_180_days: 413 intervals, observed range 91–180 days.
- first_to_second / 06_181_to_365_days: 398 intervals, observed range 181–365 days.
- first_to_second / 07_over_365_days: 82 intervals, observed range 366–609 days.

## Category continuity and movement

- Exact metric: first_to_second / category_unknown: 69 transitions (2.463406%); first_to_second / no_category_overlap: 1,435 transitions (51.231703%); first_to_second / overlap_with_change: 36 transitions (1.285255%); first_to_second / same_category_set: 1,261 transitions (45.019636%).
- Comparison: All consecutive / category_unknown: 83 transitions (2.660256%); All consecutive / no_category_overlap: 1,595 transitions (51.121795%); All consecutive / overlap_with_change: 47 transitions (1.506410%); All consecutive / same_category_set: 1,395 transitions (44.711538%).
- Interpretation: Same known category set means identical sets across the two orders; disjoint sets mean no common category; overlapping change means some shared categories with a changed set. Category pair counts cover the interval population exactly without item join multiplication.
- Limitation: Any missing category or order with no items makes the transition unknown; none is forced into same/different. Orders may have several categories. Distinct customers can appear in several transition classes and are not additive. Timestamp ties make sequence interpretation ambiguous; category movement does not prove intent or loyalty.

## Top observed categories by customer purchase group

- Exact metric: One-time #1 beleza_saude: 117,866,842 hundredths, 9.434563% of group sales, 8,162 customers; One-time #2 relogios_presentes: 111,397,403 hundredths, 8.916722% of group sales, 5,222 customers; One-time #3 cama_mesa_banho: 92,859,633 hundredths, 7.432880% of group sales, 8,430 customers; One-time #4 esporte_lazer: 88,359,442 hundredths, 7.072665% of group sales, 6,955 customers; One-time #5 informatica_acessorios: 82,814,753 hundredths, 6.628845% of group sales, 6,135 customers; Repeat #1 cama_mesa_banho: 9,483,843 hundredths, 13.019947% of group sales, 578 customers; Repeat #2 esporte_lazer: 7,125,813 hundredths, 9.782712% of group sales, 386 customers; Repeat #3 moveis_decoracao: 6,215,894 hundredths, 8.533525% of group sales, 445 customers; Repeat #4 informatica_acessorios: 6,057,708 hundredths, 8.316358% of group sales, 270 customers; Repeat #5 beleza_saude: 5,446,330 hundredths, 7.477024% of group sales, 336 customers.
- Comparison: Rankings compare one-time versus repeat customers within their own group sales denominator; all 144 group/category rows remain in JSON evidence, including missing and untranslated labels.
- Interpretation: The rankings show merchandise contribution associated with each observed customer group, after reducing item rows to order/category.
- Limitation: Category customers/orders can overlap across categories and cannot be summed. Group membership uses full observed history, so these rankings do not isolate the category of the return purchase or establish that a category causes repeat behavior.

## Limits relevant to later dashboard design

- Keep historical recency labels, original cohort sizes/denominators and all coverage flags visible. Tiny cohorts can produce extreme rates. Blank future/partial/gap rates must remain distinguishable from measured interior zeros; M0 is membership.
- Preserve the delivered-only definition, persistent-customer grain and calendar-day convention. Cohort repeat and month-specific return activity have different observation bases.
- Show conditional timing denominators and same-day/timestamp-tie counts; avoid labeling these shares as uncensored repeat likelihood. Missing categories and ambiguous states remain unknown.
- Keep monetary scale explicit; observed sales exclude freight and unsupported refund/profit adjustments. Means and segment differences do not demonstrate predictive value or natural customer classes.

These are factual findings and presentation limits. A final dashboard and strategic recommendations remain outside this stage.
