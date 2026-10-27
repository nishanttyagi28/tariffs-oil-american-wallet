-- Dollar story: FX moves since 1 Jan 2025 (USD-base pairs: >100 = USD stronger) and since the pre-war close.
select m.symbol, i.instrument_name, i.is_usd_base_fx,
       round(arg_max(m.index_2025_100, m.trade_date), 2) as latest_index_2025_100,
       round(arg_max(m.index_prewar_100, m.trade_date), 2) as latest_index_prewar_100,
       round(100 * (arg_max(m.index_2025_100, m.trade_date) / 100 - 1) * case when i.is_usd_base_fx then 1 else -1 end, 2) as usd_change_since_2025_pct
from core.fct_market_daily m join core.dim_market_instrument i using (symbol)
where i.asset_class = 'fx'
group by m.symbol, i.instrument_name, i.is_usd_base_fx order by usd_change_since_2025_pct
