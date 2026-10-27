-- What the trade war and the oil shock cost US households: prices by tariff exposure, wages, sentiment,
-- incremental customs duties per household, gasoline.
with cpi as (
    select f.month_date, d.exposure_group, d.series_id, f.yoy_pct, f.change_since_jan2025_pct
    from {{ ref('fct_cpi_monthly') }} f join {{ ref('dim_cpi_category') }} d using (series_id)
),
cpi_w as (
    select
        month_date,
        max(case when series_id = 'CUUR0000SA0' then yoy_pct end)             as cpi_headline_yoy_pct,
        max(case when series_id = 'CUUR0000SA0L1E' then yoy_pct end)          as cpi_core_yoy_pct,
        max(case when series_id = 'CUUR0000SACL1E' then yoy_pct end)          as cpi_core_goods_yoy_pct,
        max(case when series_id = 'CUUR0000SASLE' then yoy_pct end)           as cpi_core_services_yoy_pct,
        max(case when series_id = 'CUUR0000SETB01' then yoy_pct end)          as cpi_gasoline_yoy_pct,
        max(case when series_id = 'CUUR0000SAF11' then yoy_pct end)           as cpi_food_home_yoy_pct,
        avg(case when exposure_group = 'tariff_exposed_goods' then yoy_pct end) as tariff_exposed_goods_yoy_pct,
        avg(case when exposure_group = 'domestic_services' then yoy_pct end)  as domestic_services_yoy_pct,
        avg(case when exposure_group = 'tariff_exposed_goods' then change_since_jan2025_pct end) as tariff_exposed_since_jan2025_pct,
        avg(case when exposure_group = 'domestic_services' then change_since_jan2025_pct end)    as domestic_services_since_jan2025_pct
    from cpi group by month_date
)
select
    m.month_date,
    cpi_w.* exclude (month_date),
    cpi_w.tariff_exposed_goods_yoy_pct - cpi_w.domestic_services_yoy_pct   as tariff_goods_minus_services_pp,
    m.avg_hourly_earnings_usd,
    m.ahe_yoy_pct,
    m.real_wage_yoy_pct,
    m.consumer_sentiment,
    m.personal_saving_rate_pct,
    m.unemployment_rate_pct,
    m.retail_sales_yoy_pct,
    m.mortgage_30y_pct,
    m.gasoline_usd_gal,
    m.gasoline_yoy_pct,
    m.import_price_ex_fuel_yoy_pct,
    m.breakeven_10y_pct,
    cr.net_receipts_musd                                  as customs_net_musd,
    cr.gross_receipts_musd                                as customs_gross_musd,
    cr.refunds_musd                                       as customs_refunds_musd,
    cr.effective_rate_gross_pct,
    cr.incremental_gross_per_household_usd,
    cr.incremental_net_per_household_usd,
    sum(case when m.month_date >= date '2025-02-01' then coalesce(cr.incremental_gross_per_household_usd, 0) else 0 end)
        over (order by m.month_date)                      as cum_incremental_gross_per_household_usd,
    d.trade_phase,
    d.war_phase
from {{ ref('fct_macro_monthly') }} m
left join cpi_w using (month_date)
left join {{ ref('fct_customs_revenue_monthly') }} cr using (month_date)
left join {{ ref('dim_date') }} d on d.date_day = m.month_date
where m.month_date >= date '2023-01-01'