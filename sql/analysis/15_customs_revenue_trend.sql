-- Customs duties: gross, refunds (post-SCOTUS IEEPA refunds), net, YoY and the US-wide effective tariff rate.
select month_date, round(gross_receipts_musd, 0) as gross_musd, round(refunds_musd, 0) as refunds_musd,
       round(net_receipts_musd, 0) as net_musd, round(100 * net_yoy_pct, 1) as net_yoy_pct,
       round(effective_rate_gross_pct, 2) as eff_rate_gross_pct, round(effective_rate_net_pct, 2) as eff_rate_net_pct
from core.fct_customs_revenue_monthly
where month_date >= date '2024-01-01'
order by month_date
