-- DQ: recompute effective tariff rate (gross duties / goods imports) and compare with the stored column.
select month_date, gross_receipts_musd, refunds_musd, net_receipts_musd, us_imports_musd,
       round(100 * gross_receipts_musd / nullif(us_imports_musd, 0), 3) as recomputed_rate_pct,
       round(effective_rate_gross_pct, 3) as stored_rate_pct,
       round(abs(100 * gross_receipts_musd / nullif(us_imports_musd, 0) - effective_rate_gross_pct), 4) as abs_diff_pp
from core.fct_customs_revenue_monthly
where month_date >= date '2024-01-01'
order by month_date
