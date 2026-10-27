-- Incremental tariff revenue vs the 2024 run-rate, converted to $ per US household (132.2m), cumulative.
select month_date,
       round(incremental_gross_vs_2024_musd, 0) as incremental_gross_musd,
       round(incremental_gross_per_household_usd, 2) as gross_per_household_usd,
       round(sum(incremental_gross_per_household_usd) over (order by month_date), 0) as cum_gross_per_household_usd,
       round(cum_incremental_net_since_feb2025_musd, 0) as cum_incremental_net_musd
from core.fct_customs_revenue_monthly
where month_date >= date '2025-02-01'
order by month_date
