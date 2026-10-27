-- Partner-group import shares (excluding the all-partners total) sum to ~100% each month.
select month_date, sum(import_share) as s
from {{ ref('mart_trade_diversion') }}
where partner_group <> 'All partners'
group by 1
having abs(sum(import_share) - 1) > 0.02
