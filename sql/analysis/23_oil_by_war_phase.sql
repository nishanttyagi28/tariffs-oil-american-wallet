-- Brent & WTI by Iran-war phase: average, peak and change vs the pre-war close (27 Feb 2026).
select d.war_phase_order, d.war_phase, count(*) as days,
       round(avg(o.brent_usd), 2) as avg_brent, round(max(o.brent_usd), 2) as max_brent, round(min(o.brent_usd), 2) as min_brent,
       round(100 * avg(o.brent_vs_prewar_pct), 1) as avg_brent_vs_prewar_pct, round(avg(o.brent_wti_spread_usd), 2) as avg_brent_wti_spread,
       round(100 * avg(o.brent_vol_21d_ann), 1) as avg_vol_21d
from core.fct_oil_daily o join core.dim_date d on d.date_day = o.obs_date
where o.obs_date >= date '2025-01-01' and o.brent_usd is not null
group by all order by 1
