-- Event study: cumulative returns of each instrument after the Iran-war start (W02), D0..D+20.
pivot (
  select e.symbol, i.instrument_name, i.asset_class, e.window_label,
         round(case when e.symbol in ('^VIX', '^TNX') then e.level_change else 100 * e.cum_return_pct end, 2) as move
  from powerbi.mart_market_event_window e join core.dim_market_instrument i using (symbol)
  where e.event_id = 'W02'
) on window_label in ('D0', 'D+1', 'D+5', 'D+10', 'D+20') using first(move)
order by asset_class, symbol
