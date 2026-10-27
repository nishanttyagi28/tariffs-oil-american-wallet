-- Fear gauge by phase: VIX average/peak and share of days in stress (>25) or panic (>30) regimes.
select d.trade_phase, d.war_phase, count(*) as days,
       round(avg(m.close), 1) as avg_vix, round(max(m.close), 1) as max_vix,
       round(100 * avg(case when m.close > 25 then 1 else 0 end), 1) as pct_days_above_25,
       round(100 * avg(case when m.close > 30 then 1 else 0 end), 1) as pct_days_above_30
from core.fct_market_daily m join core.dim_date d on d.date_day = m.trade_date
where m.symbol = '^VIX' and m.trade_date >= date '2024-01-01'
group by all order by min(m.trade_date)
