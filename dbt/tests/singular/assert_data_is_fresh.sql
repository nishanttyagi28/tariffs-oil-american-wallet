-- Guard against a silently stale ingest: key facts must reach recent periods.
select 'trade' as src, max(month_date) as last from {{ ref('fct_trade_monthly') }} having max(month_date) < date '2026-06-01'
union all
select 'cpi', max(month_date) from {{ ref('fct_cpi_monthly') }} having max(month_date) < date '2026-07-01'
union all
select 'oil', max(obs_date) from {{ ref('fct_oil_daily') }} having max(obs_date) < date '2026-09-01'
union all
select 'markets', max(trade_date) from {{ ref('fct_market_daily') }} having max(trade_date) < date '2026-09-01'
