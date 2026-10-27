-- DQ: do Census partner-level imports add up to the US total goods imports used for the customs effective rate?
with partners as (select month_date, sum(imports_musd) as sum_partners, count(*) as n_partners from core.fct_trade_monthly group by 1)
select p.month_date, p.n_partners, round(p.sum_partners, 0) as sum_partners_musd, round(c.us_imports_musd, 0) as us_total_musd,
       round(100 * p.sum_partners / c.us_imports_musd, 2) as coverage_pct
from partners p join core.fct_customs_revenue_monthly c using (month_date)
where p.month_date >= date '2024-01-01' and c.us_imports_musd is not null
order by p.month_date
