-- Brent since 2025: running peak (window max), drawdown from peak, and the 10 biggest single-day moves.
with b as (
  select obs_date, brent_usd, brent_ret,
         max(brent_usd) over (order by obs_date) as running_peak
  from core.fct_oil_daily where obs_date >= date '2025-01-01' and brent_usd is not null
)
select obs_date, round(brent_usd, 2) as brent_usd, round(100 * brent_ret, 2) as day_ret_pct, round(running_peak, 2) as running_peak,
       round(100 * (brent_usd / running_peak - 1), 1) as drawdown_from_peak_pct
from b
qualify row_number() over (order by abs(brent_ret) desc nulls last) <= 10
order by obs_date
