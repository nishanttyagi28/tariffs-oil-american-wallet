-- Pump-price pass-through: regression slope of US gasoline ($/gal) on Brent ($/bbl), monthly, by period.
select case when month_date < date '2025-01-01' then '2015-2024' when month_date < date '2026-02-01' then '2025-Jan 2026' else 'Iran war (Feb 2026+)' end as period,
       count(*) as months,
       round(100 * regr_slope(gasoline_usd_gal, brent_usd), 2) as cents_per_gal_per_usd_bbl,
       round(regr_r2(gasoline_usd_gal, brent_usd), 3) as r2,
       round(avg(gasoline_usd_gal), 2) as avg_gasoline, round(avg(brent_usd), 2) as avg_brent
from core.fct_macro_monthly
where gasoline_usd_gal is not null and brent_usd is not null
group by 1 order by min(month_date)
