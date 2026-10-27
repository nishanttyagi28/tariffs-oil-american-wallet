-- Iran-war oil shock, daily from Oct 2025: crude prices, Strait of Hormuz transits, gasoline, VIX, S&P 500,
-- with war events annotated.
with cal as (
    select date_day as obs_date, war_phase, war_phase_order from {{ ref('dim_date') }}
    where date_day between date '2025-10-01' and current_date
),
oil as (select * from {{ ref('fct_oil_daily') }}),
hormuz as (
    select obs_date, n_total as hormuz_transits, n_tanker as hormuz_tankers, n_total_7d_avg as hormuz_transits_7d,
           n_tanker_7d_avg as hormuz_tankers_7d, total_7d_vs_prewar_pct as hormuz_7d_vs_prewar_pct
    from {{ ref('fct_chokepoint_daily') }} c join {{ ref('dim_chokepoint') }} d using (chokepoint_id)
    where d.chokepoint_name = 'Strait of Hormuz'
),
bab as (
    select obs_date, n_total_7d_avg as bab_el_mandeb_transits_7d
    from {{ ref('fct_chokepoint_daily') }} c join {{ ref('dim_chokepoint') }} d using (chokepoint_id)
    where d.chokepoint_name = 'Bab el-Mandeb Strait'
),
gas as (
    select obs_date, value as gasoline_usd_gal from {{ ref('stg_fred__series') }} where series_id = 'GASREGW'
),
mkt as (
    select trade_date as obs_date,
           max(case when symbol = '^VIX' then close end)        as vix,
           max(case when symbol = '^GSPC' then index_prewar_100 end) as sp500_prewar_100,
           max(case when symbol = 'GC=F' then close end)        as gold_usd,
           max(case when symbol = 'DX-Y.NYB' then close end)    as dxy
    from {{ ref('fct_market_daily') }} group by trade_date
),
ev as (
    select event_date as obs_date, string_agg(event, '; ') as war_event, max(category) as war_event_category
    from {{ ref('war_events') }} group by event_date
),
joined as (
    select
        cal.obs_date, cal.war_phase, cal.war_phase_order,
        oil.brent_usd, oil.wti_usd, oil.brent_source, oil.brent_vs_prewar_pct, oil.wti_vs_prewar_pct,
        oil.brent_vol_21d_ann, oil.brent_7d_avg,
        hormuz.hormuz_transits, hormuz.hormuz_tankers, hormuz.hormuz_transits_7d, hormuz.hormuz_tankers_7d,
        hormuz.hormuz_7d_vs_prewar_pct, bab.bab_el_mandeb_transits_7d,
        gas.gasoline_usd_gal, mkt.vix, mkt.sp500_prewar_100, mkt.gold_usd, mkt.dxy,
        ev.war_event, ev.war_event_category
    from cal
    left join oil on oil.obs_date = cal.obs_date
    left join hormuz on hormuz.obs_date = cal.obs_date
    left join bab on bab.obs_date = cal.obs_date
    left join gas on gas.obs_date = cal.obs_date
    left join mkt on mkt.obs_date = cal.obs_date
    left join ev on ev.obs_date = cal.obs_date
)
select
    joined.* exclude (gasoline_usd_gal),
    -- weekly gasoline price carried forward to daily grain
    last_value(gasoline_usd_gal ignore nulls) over (order by obs_date rows between unbounded preceding and current row)
        as gasoline_usd_gal,
    obs_date >= date '{{ var("war_start") }}' as is_war_period
from joined