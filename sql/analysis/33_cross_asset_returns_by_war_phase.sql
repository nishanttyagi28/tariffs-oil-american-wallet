-- Cross-asset scorecard: compounded return of each instrument within each Iran-war phase (exp(sum(log_ret))).
select i.asset_class, m.symbol, i.instrument_name, d.war_phase_order, d.war_phase,
       round(100 * (exp(sum(m.log_ret)) - 1), 2) as phase_return_pct,
       round(100 * stddev_samp(m.ret) * sqrt(252), 1) as ann_vol_pct
from core.fct_market_daily m join core.dim_market_instrument i using (symbol) join core.dim_date d on d.date_day = m.trade_date
where m.trade_date >= date '2025-12-01' and m.log_ret is not null
group by all order by i.asset_class, m.symbol, d.war_phase_order
