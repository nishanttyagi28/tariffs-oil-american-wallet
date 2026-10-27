-- DQ: row counts and coverage window of every fact table (is the warehouse fresh?).
select 'fct_trade_monthly' as tbl, count(*) as n_rows, min(month_date) as first_period, max(month_date) as last_period from core.fct_trade_monthly
union all select 'fct_tariff_rate_monthly', count(*), min(month_date), max(month_date) from core.fct_tariff_rate_monthly
union all select 'fct_customs_revenue_monthly', count(*), min(month_date), max(month_date) from core.fct_customs_revenue_monthly
union all select 'fct_cpi_monthly', count(*), min(month_date), max(month_date) from core.fct_cpi_monthly
union all select 'fct_macro_monthly', count(*), min(month_date), max(month_date) from core.fct_macro_monthly
union all select 'fct_market_daily', count(*), min(trade_date), max(trade_date) from core.fct_market_daily
union all select 'fct_oil_daily', count(*), min(obs_date), max(obs_date) from core.fct_oil_daily
union all select 'fct_chokepoint_daily', count(*), min(obs_date), max(obs_date) from core.fct_chokepoint_daily
order by tbl
