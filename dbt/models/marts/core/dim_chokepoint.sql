-- 28 maritime chokepoints (IMF PortWatch) with location and traffic baselines.
with d as (select * from {{ ref('stg_portwatch__chokepoints_daily') }}),
stats as (
    select
        chokepoint_id,
        avg(case when year(obs_date) = 2024 then n_total end)                                  as avg_daily_transits_2024,
        avg(case when obs_date between date '2026-01-01' and date '{{ var("prewar_date") }}' then n_total end)
                                                                                               as avg_daily_transits_prewar,
        avg(case when obs_date > (select max(obs_date) from d) - interval 30 day then n_total end) as avg_daily_transits_last30,
        avg(case when year(obs_date) = 2024 then n_tanker end)                                 as avg_daily_tankers_2024,
        max(obs_date)                                                                          as last_obs_date
    from d group by chokepoint_id
)
select
    r.chokepoint_id,
    r.chokepoint_name,
    r.latitude,
    r.longitude,
    r.chokepoint_name in ('Strait of Hormuz', 'Bab el-Mandeb Strait', 'Suez Canal', 'Malacca Strait',
                          'Panama Canal', 'Cape of Good Hope', 'Bosporus Strait')          as is_energy_route,
    s.avg_daily_transits_2024,
    s.avg_daily_transits_prewar,
    s.avg_daily_transits_last30,
    s.avg_daily_tankers_2024,
    s.avg_daily_transits_last30 / nullif(s.avg_daily_transits_prewar, 0) - 1                 as last30_vs_prewar_pct,
    s.last_obs_date
from {{ ref('stg_portwatch__chokepoints_ref') }} r
left join stats s using (chokepoint_id)