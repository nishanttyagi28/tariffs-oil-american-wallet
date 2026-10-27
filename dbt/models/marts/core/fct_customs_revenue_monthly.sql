-- US customs duties (Treasury Monthly Treasury Statement, $M): gross, refunds, net; effective tariff rate proxy
-- = duties / Census goods imports of the same month; incremental duties vs 2024 average and per-household cost.
with c as (select * from {{ ref('stg_treasury__customs') }}),
imp as (
    select month_date, sum(imports_musd) as us_imports_musd
    from {{ ref('fct_trade_monthly') }} group by month_date
),
base as (
    select avg(net_receipts_musd) as net_2024_avg_musd, avg(gross_receipts_musd) as gross_2024_avg_musd
    from c where year(month_date) = {{ var('baseline_year') }}
),
j as (
    select
        c.month_date,
        c.gross_receipts_musd,
        c.refunds_musd,
        c.net_receipts_musd,
        imp.us_imports_musd,
        100 * c.gross_receipts_musd / nullif(imp.us_imports_musd, 0)   as effective_rate_gross_pct,
        100 * c.net_receipts_musd / nullif(imp.us_imports_musd, 0)     as effective_rate_net_pct,
        c.net_receipts_musd - base.net_2024_avg_musd                   as incremental_net_vs_2024_musd,
        c.gross_receipts_musd - base.gross_2024_avg_musd               as incremental_gross_vs_2024_musd
    from c
    cross join base
    left join imp on imp.month_date = c.month_date
)
select
    j.*,
    j.net_receipts_musd / nullif(ly.net_receipts_musd, 0) - 1                              as net_yoy_pct,
    sum(case when j.month_date >= date '2025-02-01' then j.incremental_net_vs_2024_musd else 0 end)
        over (order by j.month_date)                                                        as cum_incremental_net_since_feb2025_musd,
    j.incremental_gross_vs_2024_musd * 1e6 / ({{ var('us_households_m') }} * 1e6)            as incremental_gross_per_household_usd,
    j.incremental_net_vs_2024_musd * 1e6 / ({{ var('us_households_m') }} * 1e6)              as incremental_net_per_household_usd
from j
left join j ly on ly.month_date = cast(j.month_date - interval 12 month as date)