{{ config(materialized='table') }}
-- Daily returns per instrument with a trading-day index (used for event windows and rolling stats).
select
    p.trade_date,
    p.symbol,
    p.close,
    p.adj_close,
    p.adj_close / lag(p.adj_close) over w - 1                as ret,
    ln(p.adj_close / lag(p.adj_close) over w)                as log_ret,
    row_number() over w                                      as trading_day_idx
from {{ ref('stg_yahoo__prices') }} p
window w as (partition by p.symbol order by p.trade_date)