-- Event study: cumulative returns of every instrument around each tariff and war event.
-- t0 = first trading day on/after the event date; base = close of the prior trading day (t-1).
with events as (
    select event_id, event_date, 'tariff' as event_family, measure as event_name, country_iso3 as event_country
    from {{ ref('tariff_events') }}
    union all
    select event_id, event_date, 'war', event, 'IRN'
    from {{ ref('war_events') }} where category <> 'baseline'
),
r as (select symbol, trade_date, adj_close, trading_day_idx from {{ ref('int_market__returns') }}),
syms as (select distinct symbol from r),
-- ASOF join: first trading day on/after the event date, per symbol (avoids a large inequality join).
t0 as (
    select e.*, s.symbol, r.trading_day_idx as t0_idx
    from events e
    cross join syms s
    asof join r on r.symbol = s.symbol and r.trade_date >= e.event_date
),
windows as (
    select * from (values ('D0', 0), ('D+1', 1), ('D+5', 4), ('D+10', 9), ('D+20', 19)) as w(window_label, k)
)
select
    t0.event_id, t0.event_date, t0.event_family, t0.event_name, t0.event_country, t0.symbol,
    w.window_label,
    w.k + 1                                                as window_days,
    pre.trade_date                                         as base_date,
    post.trade_date                                        as end_date,
    pre.adj_close                                          as base_close,
    post.adj_close                                         as end_close,
    post.adj_close / pre.adj_close - 1                     as cum_return_pct,
    case when t0.symbol in ('^VIX', '^TNX') then post.adj_close - pre.adj_close end as level_change
from t0
cross join windows w
join r pre  on pre.symbol = t0.symbol and pre.trading_day_idx = t0.t0_idx - 1
join r post on post.symbol = t0.symbol and post.trading_day_idx = t0.t0_idx + w.k