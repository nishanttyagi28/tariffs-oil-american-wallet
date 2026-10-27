-- Which global chokepoints changed most: last 30 days vs pre-war average transits (RANK by disruption).
select rank() over (order by last30_vs_prewar_pct) as disruption_rank, chokepoint_name, is_energy_route,
       round(avg_daily_transits_2024, 1) as avg_2024, round(avg_daily_transits_prewar, 1) as avg_prewar,
       round(avg_daily_transits_last30, 1) as avg_last30, round(100 * last30_vs_prewar_pct, 1) as last30_vs_prewar_pct, last_obs_date
from core.dim_chokepoint
order by disruption_rank
