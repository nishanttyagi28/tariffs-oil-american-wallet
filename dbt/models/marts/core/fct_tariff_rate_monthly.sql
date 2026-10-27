-- Monthly statutory additional headline tariff per partner (avg of daily seed schedule via dim_country.tariff_schedule_key)
-- plus an 'ALL' row: 2024-import-weighted statutory rate and the Treasury/Census effective-rate proxy.
with daily as (select * from {{ ref('int_tariff__headline_daily') }}),
monthly_key as (
    select cast(date_trunc('month', obs_date) as date) as month_date, schedule_key,
           avg(headline_rate_pct) as statutory_rate_pct, max(headline_rate_pct) as max_rate_in_month_pct,
           bool_and(verified) as all_days_verified
    from daily group by all
),
countries as (
    select country_iso3, tariff_schedule_key from {{ ref('dim_country') }}
    where entity_type = 'country' and is_us_trade_partner
),
w2024 as (
    select country_iso3, sum(imports_musd) / sum(sum(imports_musd)) over () as weight_2024
    from {{ ref('fct_trade_monthly') }} where year(month_date) = {{ var('baseline_year') }} group by country_iso3
),
per_country as (
    select mk.month_date, c.country_iso3, c.tariff_schedule_key, mk.statutory_rate_pct, mk.max_rate_in_month_pct,
           mk.all_days_verified, cast(null as double) as effective_rate_gross_pct, cast(null as double) as effective_rate_net_pct
    from countries c
    join monthly_key mk on mk.schedule_key = c.tariff_schedule_key
),
eu_row as (
    select month_date, 'EUU' as country_iso3, schedule_key as tariff_schedule_key, statutory_rate_pct, max_rate_in_month_pct,
           all_days_verified, cast(null as double), cast(null as double)
    from monthly_key where schedule_key = 'EUU'
),
all_row as (
    select pc.month_date, 'ALL' as country_iso3, 'WEIGHTED' as tariff_schedule_key,
           sum(pc.statutory_rate_pct * coalesce(w.weight_2024, 0))      as statutory_rate_pct,
           max(pc.max_rate_in_month_pct)                                as max_rate_in_month_pct,
           bool_and(pc.all_days_verified)                               as all_days_verified,
           any_value(cr.effective_rate_gross_pct)                       as effective_rate_gross_pct,
           any_value(cr.effective_rate_net_pct)                         as effective_rate_net_pct
    from per_country pc
    left join w2024 w on w.country_iso3 = pc.country_iso3
    left join {{ ref('fct_customs_revenue_monthly') }} cr on cr.month_date = pc.month_date
    group by pc.month_date
)
select * from per_country
union all select * from eu_row
union all select * from all_row