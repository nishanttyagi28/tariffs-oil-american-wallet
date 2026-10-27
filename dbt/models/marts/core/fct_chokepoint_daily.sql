-- Daily chokepoint transits with 7-day averages and comparisons to 2024 and pre-war (Jan 1 - Feb 27 2026) baselines.
with d as (select * from {{ ref('stg_portwatch__chokepoints_daily') }}),
b as (select chokepoint_id, avg_daily_transits_2024, avg_daily_transits_prewar, avg_daily_tankers_2024
      from {{ ref('dim_chokepoint') }}),
pw as (
    select chokepoint_id, avg(n_tanker) as avg_daily_tankers_prewar
    from d where obs_date between date '2026-01-01' and date '{{ var("prewar_date") }}' group by chokepoint_id
)
select
    d.obs_date,
    d.chokepoint_id,
    d.n_total, d.n_tanker, d.n_container, d.n_dry_bulk, d.n_cargo,
    d.capacity_dwt, d.capacity_tanker_dwt,
    avg(d.n_total) over w7                                          as n_total_7d_avg,
    avg(d.n_tanker) over w7                                         as n_tanker_7d_avg,
    avg(d.n_total) over w7 / nullif(b.avg_daily_transits_2024, 0) - 1   as total_7d_vs_2024_pct,
    avg(d.n_total) over w7 / nullif(b.avg_daily_transits_prewar, 0) - 1 as total_7d_vs_prewar_pct,
    avg(d.n_tanker) over w7 / nullif(pw.avg_daily_tankers_prewar, 0) - 1 as tanker_7d_vs_prewar_pct
from d
left join b using (chokepoint_id)
left join pw using (chokepoint_id)
window w7 as (partition by d.chokepoint_id order by d.obs_date rows between 6 preceding and current row)