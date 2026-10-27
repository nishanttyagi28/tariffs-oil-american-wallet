-- Lead-lag: correlation of import-price (ex fuel) YoY with core-goods CPI YoY k months later (k = 0..9), 2017+.
with ip as (select month_date, import_price_ex_fuel_yoy_pct as x from core.fct_macro_monthly where import_price_ex_fuel_yoy_pct is not null),
cg as (select month_date, yoy_pct as y from core.fct_cpi_monthly where series_id = 'CUUR0000SACL1E' and yoy_pct is not null),
lags as (select unnest(range(0, 10)) as k)
select k as lag_months, count(*) as n, round(corr(ip.x, cg.y), 3) as correlation
from lags join ip on true join cg on cg.month_date = ip.month_date + to_months(k)
where ip.month_date >= date '2017-01-01'
group by k order by k
