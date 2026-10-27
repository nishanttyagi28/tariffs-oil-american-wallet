-- US total goods trade (sum over partners): monthly balance, rolling 12-month sum (window frame) and YoY change, 2023+.
with us as (select month_date, sum(imports_musd) as imports_musd, sum(exports_musd) as exports_musd, sum(balance_musd) as balance_musd from core.fct_trade_monthly group by 1)
select month_date, round(imports_musd, 0) as imports_musd, round(exports_musd, 0) as exports_musd, round(balance_musd, 0) as balance_musd,
       round(sum(balance_musd) over (order by month_date rows between 11 preceding and current row), 0) as balance_r12m_musd,
       round(balance_musd - lag(balance_musd, 12) over (order by month_date), 0) as balance_yoy_change_musd
from us
qualify month_date >= date '2023-01-01'
order by month_date
