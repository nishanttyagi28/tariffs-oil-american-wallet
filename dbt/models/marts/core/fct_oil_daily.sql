-- Daily crude oil: EIA spot (Brent, WTI) plus Yahoo front-month futures (extends past the EIA publication lag).
with spot as (
    select obs_date,
           max(case when benchmark = 'brent' then price_usd_bbl end) as brent_spot_usd,
           max(case when benchmark = 'wti' then price_usd_bbl end)   as wti_spot_usd
    from {{ ref('stg_eia__crude_spot') }} where obs_date >= date '2015-01-01' group by obs_date
),
fut as (
    select trade_date as obs_date,
           max(case when symbol = 'BZ=F' then close end) as brent_futures_usd,
           max(case when symbol = 'CL=F' then close end) as wti_futures_usd
    from {{ ref('stg_yahoo__prices') }} where symbol in ('BZ=F', 'CL=F') group by trade_date
),
j as (
    select
        coalesce(spot.obs_date, fut.obs_date)                                   as obs_date,
        spot.brent_spot_usd, spot.wti_spot_usd, fut.brent_futures_usd, fut.wti_futures_usd,
        coalesce(spot.brent_spot_usd, fut.brent_futures_usd)                    as brent_usd,
        coalesce(spot.wti_spot_usd, fut.wti_futures_usd)                        as wti_usd,
        case when spot.brent_spot_usd is not null then 'EIA spot' else 'Yahoo futures' end as brent_source
    from spot full outer join fut on fut.obs_date = spot.obs_date
),
prewar as (
    select arg_max(brent_usd, obs_date) as brent_prewar, arg_max(wti_usd, obs_date) as wti_prewar
    from j where obs_date <= date '{{ var("prewar_date") }}' and brent_usd is not null
),
k as (
    select j.*,
           ln(brent_usd / lag(brent_usd) over w)                                as brent_log_ret
    from j where brent_usd is not null
    window w as (order by obs_date)
)
select
    k.obs_date,
    k.brent_spot_usd, k.wti_spot_usd, k.brent_futures_usd, k.wti_futures_usd,
    k.brent_usd, k.wti_usd, k.brent_source,
    k.brent_usd - k.wti_usd                                                     as brent_wti_spread_usd,
    k.brent_usd / nullif(lag(k.brent_usd) over w, 0) - 1                        as brent_ret,
    stddev_samp(k.brent_log_ret) over (order by k.obs_date rows between 20 preceding and current row) * sqrt(252)
                                                                                as brent_vol_21d_ann,
    k.brent_usd / max(k.brent_usd) over (order by k.obs_date rows between 251 preceding and current row) - 1
                                                                                as brent_drawdown_52w_pct,
    k.brent_usd / nullif(prewar.brent_prewar, 0) - 1                            as brent_vs_prewar_pct,
    k.wti_usd / nullif(prewar.wti_prewar, 0) - 1                                as wti_vs_prewar_pct,
    avg(k.brent_usd) over (order by k.obs_date rows between 6 preceding and current row) as brent_7d_avg
from k cross join prewar
window w as (order by k.obs_date)