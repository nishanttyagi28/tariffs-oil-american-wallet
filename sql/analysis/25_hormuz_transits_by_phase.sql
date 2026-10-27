-- Strait of Hormuz daily transits (all ships / tankers) by war phase vs the 2024 average (IMF PortWatch).
with base as (select avg(n_total) as t24, avg(n_tanker) as k24 from core.fct_chokepoint_daily
              where chokepoint_id = 'chokepoint6' and year(obs_date) = 2024)
select d.war_phase_order, d.war_phase, count(*) as days,
       round(avg(c.n_total), 1) as avg_transits, round(avg(c.n_tanker), 1) as avg_tankers,
       round(100 * (avg(c.n_total) / base.t24 - 1), 1) as transits_vs_2024_pct,
       round(100 * (avg(c.n_tanker) / base.k24 - 1), 1) as tankers_vs_2024_pct
from core.fct_chokepoint_daily c join core.dim_date d on d.date_day = c.obs_date cross join base
where c.chokepoint_id = 'chokepoint6' and c.obs_date >= date '2025-06-01'
group by d.war_phase_order, d.war_phase, base.t24, base.k24 order by 1
