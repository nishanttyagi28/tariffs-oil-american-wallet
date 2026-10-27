-- Maximum drawdown since 1 Jan 2025 per equity index, with trough date, and recovery to latest.
with x as (
  select m.symbol, i.instrument_name, m.trade_date, m.drawdown_since_2025_pct, m.index_2025_100
  from core.fct_market_daily m join core.dim_market_instrument i using (symbol)
  where i.asset_class = 'equity_index' and m.trade_date >= date '2025-01-01'
)
select symbol, instrument_name,
       round(100 * min(drawdown_since_2025_pct), 1) as max_drawdown_pct,
       arg_min(trade_date, drawdown_since_2025_pct) as trough_date,
       round(arg_max(index_2025_100, trade_date), 1) as latest_index_2025_100
from x group by all order by max_drawdown_pct
