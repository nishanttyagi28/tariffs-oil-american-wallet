-- Wide monthly US macro panel (FRED monthly averages + NY Fed GSCPI) with derived YoY and real-wage metrics.
with f as (select * from {{ ref('int_fred__monthly') }}),
months as (
    select distinct month_date from f where month_date >= date '2015-01-01'
),
p as (
    select
        m.month_date,
        max(case when series_id = 'CPIAUCSL' then value end)        as cpi_sa,
        max(case when series_id = 'CPILFESL' then value end)        as core_cpi_sa,
        max(case when series_id = 'PCEPI' then value end)           as pce_index,
        max(case when series_id = 'PCEPILFE' then value end)        as core_pce_index,
        max(case when series_id = 'CES0500000003' then value end)   as avg_hourly_earnings_usd,
        max(case when series_id = 'UNRATE' then value end)          as unemployment_rate_pct,
        max(case when series_id = 'PAYEMS' then value end)          as nonfarm_payrolls_k,
        max(case when series_id = 'UMCSENT' then value end)         as consumer_sentiment,
        max(case when series_id = 'PSAVERT' then value end)         as personal_saving_rate_pct,
        max(case when series_id = 'RSAFS' then value end)           as retail_sales_musd,
        max(case when series_id = 'IR' then value end)              as import_price_index,
        max(case when series_id = 'IREXFDFLS' then value end)       as import_price_ex_food_fuel,
        max(case when series_id = 'IREXPET' then value end)         as import_price_ex_petroleum,
        max(case when series_id = 'BOPGSTB' then value end)         as trade_balance_gs_musd,
        max(case when series_id = 'GASREGW' then value end)         as gasoline_usd_gal,
        max(case when series_id = 'MORTGAGE30US' then value end)    as mortgage_30y_pct,
        max(case when series_id = 'FEDFUNDS' then value end)        as fed_funds_pct,
        max(case when series_id = 'DGS10' then value end)           as ust_10y_pct,
        max(case when series_id = 'DGS2' then value end)            as ust_2y_pct,
        max(case when series_id = 'T10YIE' then value end)          as breakeven_10y_pct,
        max(case when series_id = 'DTWEXBGS' then value end)        as usd_broad_index,
        max(case when series_id = 'VIXCLS' then value end)          as vix,
        max(case when series_id = 'DCOILBRENTEU' then value end)    as brent_usd,
        max(case when series_id = 'DCOILWTICO' then value end)      as wti_usd,
        max(case when series_id = 'DHHNGSP' then value end)         as henry_hub_usd
    from months m
    left join f using (month_date)
    group by m.month_date
),
g as (select month_date, gscpi from {{ ref('stg_gscpi__monthly') }})
select
    p.*,
    g.gscpi,
    p.ust_10y_pct - p.ust_2y_pct                                                      as yield_curve_10y2y_pct,
    p.cpi_sa / nullif(lag(p.cpi_sa, 12) over w, 0) - 1                                as cpi_yoy_pct,
    p.core_cpi_sa / nullif(lag(p.core_cpi_sa, 12) over w, 0) - 1                      as core_cpi_yoy_pct,
    p.pce_index / nullif(lag(p.pce_index, 12) over w, 0) - 1                          as pce_yoy_pct,
    p.avg_hourly_earnings_usd / nullif(lag(p.avg_hourly_earnings_usd, 12) over w, 0) - 1 as ahe_yoy_pct,
    (p.avg_hourly_earnings_usd / nullif(lag(p.avg_hourly_earnings_usd, 12) over w, 0))
      / (p.cpi_sa / nullif(lag(p.cpi_sa, 12) over w, 0)) - 1                          as real_wage_yoy_pct,
    p.retail_sales_musd / nullif(lag(p.retail_sales_musd, 12) over w, 0) - 1          as retail_sales_yoy_pct,
    p.import_price_ex_food_fuel / nullif(lag(p.import_price_ex_food_fuel, 12) over w, 0) - 1 as import_price_ex_fuel_yoy_pct,
    p.gasoline_usd_gal / nullif(lag(p.gasoline_usd_gal, 12) over w, 0) - 1            as gasoline_yoy_pct,
    p.cpi_sa / nullif(lag(p.cpi_sa, 1) over w, 0) - 1                                 as cpi_mom_pct
from p
left join g using (month_date)
window w as (order by p.month_date)