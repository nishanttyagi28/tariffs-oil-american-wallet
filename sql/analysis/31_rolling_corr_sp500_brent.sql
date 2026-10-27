-- Rolling 63-trading-day correlation of S&P 500 and Brent daily log returns (window aggregate), month-end values.
with r as (
  select trade_date,
         max(log_ret) filter (where symbol = '^GSPC') as spx,
         max(log_ret) filter (where symbol = 'BZ=F') as brent,
         max(log_ret) filter (where symbol = 'GC=F') as gold
  from core.fct_market_daily where symbol in ('^GSPC', 'BZ=F', 'GC=F') group by 1
), w as (
  select trade_date,
         corr(spx, brent) over (order by trade_date rows between 62 preceding and current row) as corr_spx_brent,
         corr(spx, gold)  over (order by trade_date rows between 62 preceding and current row) as corr_spx_gold
  from r
)
select date_trunc('month', trade_date) as month, round(corr_spx_brent, 3) as corr_spx_brent_63d, round(corr_spx_gold, 3) as corr_spx_gold_63d
from w where trade_date >= date '2024-06-01'
qualify row_number() over (partition by date_trunc('month', trade_date) order by trade_date desc) = 1
order by month
