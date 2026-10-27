-- US total imports/exports by tariff-war phase (dim_date phases from seeds/event_phases.csv), 2024 onward.
with us as (select month_date, sum(imports_musd) as imports_musd, sum(exports_musd) as exports_musd, sum(balance_musd) as balance_musd from core.fct_trade_monthly group by 1)
select d.trade_phase_order, d.trade_phase, count(*) as months,
       round(avg(us.imports_musd), 0) as avg_monthly_imports_musd,
       round(avg(us.exports_musd), 0) as avg_monthly_exports_musd,
       round(avg(us.balance_musd), 0) as avg_monthly_balance_musd
from us join core.dim_date d on d.date_day = us.month_date
where us.month_date >= date '2024-01-01'
group by all order by 1
