-- China: monthly imports with MoM change (LAG) and a 3-month moving average, 2024 onward.
select month_date,
       round(imports_musd, 0) as imports_musd,
       round(100 * (imports_musd / lag(imports_musd) over w - 1), 1) as mom_pct,
       round(avg(imports_musd) over (w rows between 2 preceding and current row), 0) as imports_3m_avg,
       round(100 * share_of_us_imports, 2) as share_of_us_imports_pct
from core.fct_trade_monthly
where country_iso3 = 'CHN' and month_date >= date '2023-12-01'
window w as (order by month_date)
order by month_date
