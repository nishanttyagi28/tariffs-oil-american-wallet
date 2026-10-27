-- Event study: Liberation Day (T05, 2 Apr 2025) and the 90-day pause (T07): equity index returns by window.
select e.event_id, e.event_name, e.symbol, i.instrument_name, e.window_label, round(100 * e.cum_return_pct, 2) as cum_return_pct,
       rank() over (partition by e.event_id, e.window_label order by e.cum_return_pct) as worst_rank
from powerbi.mart_market_event_window e join core.dim_market_instrument i using (symbol)
where e.event_id in ('T05', 'T07') and i.asset_class = 'equity_index' and e.window_label in ('D0', 'D+5', 'D+20')
order by e.event_id, e.window_label, worst_rank
