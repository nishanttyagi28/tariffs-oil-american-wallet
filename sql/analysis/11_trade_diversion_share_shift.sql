-- Trade diversion: each partner group's share of US imports, 2024 vs the latest 6 months, and implied diverted $.
with last6 as (
  select partner_group, avg(import_share) as share_last6, avg(import_share_2024) as share_2024,
         sum(diverted_imports_musd) as diverted_last6_musd
  from powerbi.mart_trade_diversion
  where month_date > (select max(month_date) from powerbi.mart_trade_diversion) - interval 6 month
    and partner_group <> 'All partners'
  group by 1
)
select partner_group, round(100 * share_2024, 2) as share_2024_pct, round(100 * share_last6, 2) as share_last6m_pct,
       round(100 * (share_last6 - share_2024), 2) as share_change_pp, round(diverted_last6_musd, 0) as diverted_last6m_musd
from last6 order by share_change_pp desc
