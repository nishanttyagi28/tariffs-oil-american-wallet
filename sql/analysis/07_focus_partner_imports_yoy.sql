-- Year-over-year import growth for focus partners over the last 8 reported months (LAG-based YoY).
select month_date, country_iso3, round(imports_musd, 0) as imports_musd,
       round(imports_musd_ly, 0) as imports_same_month_ly, round(100 * imports_yoy_pct, 1) as imports_yoy_pct
from core.fct_trade_monthly
where country_iso3 in ('CHN','CAN','MEX','IND','DEU','JPN','VNM','TWN','KOR','CHE','GBR')
  and month_date > (select max(month_date) from core.fct_trade_monthly) - interval 8 month
order by country_iso3, month_date
