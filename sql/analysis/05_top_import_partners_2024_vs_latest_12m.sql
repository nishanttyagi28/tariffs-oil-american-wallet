-- Top 15 US import partners: calendar-2024 total vs the latest rolling 12 months, with RANK() shift.
with latest as (select max(month_date) as m from core.fct_trade_monthly),
base as (
  select country_iso3, sum(imports_musd) as imports_2024
  from core.fct_trade_monthly where year(month_date) = 2024 group by 1
),
r12 as (
  select t.country_iso3, t.imports_r12m_musd as imports_last12m
  from core.fct_trade_monthly t, latest where t.month_date = latest.m
),
j as (
  select d.country_name, b.country_iso3, b.imports_2024, r.imports_last12m,
         rank() over (order by b.imports_2024 desc) as rank_2024,
         rank() over (order by r.imports_last12m desc) as rank_last12m
  from base b join r12 r using (country_iso3) join core.dim_country d using (country_iso3)
  where d.entity_type = 'country'
)
select *, rank_2024 - rank_last12m as rank_gain,
       round(100 * (imports_last12m / imports_2024 - 1), 1) as change_pct
from j where rank_2024 <= 15 or rank_last12m <= 15
order by rank_last12m
