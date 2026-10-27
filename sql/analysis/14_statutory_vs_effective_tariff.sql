-- Statutory (2024-import-weighted headline) tariff vs the effective rate actually collected (customs gross & net / imports).
select month_date, round(statutory_rate_pct, 2) as weighted_statutory_pct, max_rate_in_month_pct as max_partner_rate_pct,
       round(effective_rate_gross_pct, 2) as effective_gross_pct, round(effective_rate_net_pct, 2) as effective_net_pct,
       round(statutory_rate_pct - effective_rate_gross_pct, 2) as statutory_minus_effective_pp
from core.fct_tariff_rate_monthly
where country_iso3 = 'ALL' and month_date between date '2024-01-01' and (select max(month_date) from core.fct_trade_monthly)
order by month_date
