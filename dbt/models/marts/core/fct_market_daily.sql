-- Daily market panel: returns, 21-day annualised volatility, drawdowns, rebased indices (2025 start and pre-war).
with r as (select * from {{ ref('int_market__returns') }}),
base25 as (
    select symbol, arg_min(adj_close, trade_date) as base_2025 from r where trade_date >= date '2025-01-01' group by symbol
),
baseprewar as (
    select symbol, arg_max(adj_close, trade_date) as base_prewar
    from r where trade_date <= date '{{ var("prewar_date") }}' group by symbol
),
x as (
    select
        r.*,
        stddev_samp(r.log_ret) over (partition by r.symbol order by r.trade_date rows between 20 preceding and current row)
            * sqrt(252)                                                                  as vol_21d_ann,
        stddev_samp(r.log_ret) over (partition by r.symbol order by r.trade_date rows between 62 preceding and current row)
            * sqrt(252)                                                                  as vol_63d_ann,
        max(r.adj_close) over (partition by r.symbol order by r.trade_date rows between unbounded preceding and current row)
                                                                                         as running_max,
        max(case when r.trade_date >= date '2025-01-01' then r.adj_close end)
            over (partition by r.symbol order by r.trade_date rows between unbounded preceding and current row)
                                                                                         as running_max_2025,
        avg(r.adj_close) over (partition by r.symbol order by r.trade_date rows between 49 preceding and current row)
                                                                                         as sma_50,
        avg(r.adj_close) over (partition by r.symbol order by r.trade_date rows between 199 preceding and current row)
                                                                                         as sma_200
    from r
)
select
    x.trade_date,
    x.symbol,
    x.close,
    x.adj_close,
    x.ret,
    x.log_ret,
    x.trading_day_idx,
    x.vol_21d_ann,
    x.vol_63d_ann,
    x.adj_close / x.running_max - 1                                                    as drawdown_pct,
    case when x.trade_date >= date '2025-01-01' then x.adj_close / x.running_max_2025 - 1 end as drawdown_since_2025_pct,
    100 * x.adj_close / b25.base_2025                                                  as index_2025_100,
    100 * x.adj_close / bpw.base_prewar                                                as index_prewar_100,
    x.sma_50,
    x.sma_200,
    case when x.adj_close > x.sma_200 then 'above' else 'below' end                    as trend_vs_sma200
from x
left join base25 b25 using (symbol)
left join baseprewar bpw using (symbol)