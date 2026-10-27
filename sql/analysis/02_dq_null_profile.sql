-- DQ: null-rate profile of key measures since 2024 (gaps that the dashboard must handle).
select 'fct_macro_monthly' as tbl, column_name, round(100.0 * null_cnt / n, 1) as null_pct
from (
  unpivot (
    select count(*) as n,
           count(*) - count(cpi_sa) as cpi_sa, count(*) - count(core_cpi_sa) as core_cpi_sa,
           count(*) - count(avg_hourly_earnings_usd) as avg_hourly_earnings_usd,
           count(*) - count(consumer_sentiment) as consumer_sentiment,
           count(*) - count(gasoline_usd_gal) as gasoline_usd_gal,
           count(*) - count(brent_usd) as brent_usd,
           count(*) - count(import_price_ex_food_fuel) as import_price_ex_food_fuel,
           count(*) - count(gscpi) as gscpi
    from core.fct_macro_monthly where month_date >= date '2024-01-01'
  ) on cpi_sa, core_cpi_sa, avg_hourly_earnings_usd, consumer_sentiment, gasoline_usd_gal, brent_usd, import_price_ex_food_fuel, gscpi
  into name column_name value null_cnt
)
order by null_pct desc
