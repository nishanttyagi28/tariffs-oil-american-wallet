-- India lens: US-India trade, tariff rate, INR and Nifty by month (2024 onward).
with mkt as (
  select date_trunc('month', trade_date) as month_date,
         avg(close) filter (where symbol = 'INR=X') as usd_inr,
         avg(close) filter (where symbol = '^NSEI') as nifty
  from core.fct_market_daily where symbol in ('INR=X', '^NSEI') group by 1
)
select t.month_date, round(t.imports_musd, 0) as us_imports_from_india_musd, round(t.exports_musd, 0) as us_exports_to_india_musd,
       round(t.balance_musd, 0) as balance_musd, round(100 * t.imports_yoy_pct, 1) as imports_yoy_pct,
       r.statutory_rate_pct as us_tariff_on_india_pct, round(mkt.usd_inr, 2) as usd_inr, round(mkt.nifty, 0) as nifty_avg
from core.fct_trade_monthly t
left join core.fct_tariff_rate_monthly r on r.country_iso3 = t.country_iso3 and r.month_date = t.month_date
left join mkt on mkt.month_date = t.month_date
where t.country_iso3 = 'IND' and t.month_date >= date '2024-01-01'
order by t.month_date
