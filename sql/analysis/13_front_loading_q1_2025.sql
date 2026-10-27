-- Front-loading ahead of tariffs: Jan-Mar 2025 imports vs Jan-Mar 2024, then Apr-Jun 2025 hangover.
select country_iso3,
       round(sum(imports_musd) filter (where month_date between date '2024-01-01' and date '2024-03-01'), 0) as q1_2024,
       round(sum(imports_musd) filter (where month_date between date '2025-01-01' and date '2025-03-01'), 0) as q1_2025,
       round(100 * (sum(imports_musd) filter (where month_date between date '2025-01-01' and date '2025-03-01')
            / sum(imports_musd) filter (where month_date between date '2024-01-01' and date '2024-03-01') - 1), 1) as q1_yoy_pct,
       round(100 * (sum(imports_musd) filter (where month_date between date '2025-04-01' and date '2025-06-01')
            / sum(imports_musd) filter (where month_date between date '2024-04-01' and date '2024-06-01') - 1), 1) as q2_yoy_pct
from (select month_date, country_iso3, imports_musd from core.fct_trade_monthly
      where country_iso3 in ('CHN','CAN','MEX','IND','JPN','VNM','TWN','KOR','CHE','GBR','DEU','IRL')
      union all select month_date, 'US_TOTAL', imports_musd from (select month_date, sum(imports_musd) as imports_musd, sum(exports_musd) as exports_musd, sum(balance_musd) as balance_musd from core.fct_trade_monthly group by 1))
group by 1 order by q1_yoy_pct desc
