select cast(date as date) as trade_date, symbol, cast(open as double) as open, cast(high as double) as high,
       cast(low as double) as low, cast(close as double) as close, cast(adj_close as double) as adj_close,
       cast(volume as double) as volume
from {{ raw('yahoo', 'market_prices_daily') }}
where close is not null and close > 0
qualify row_number() over (partition by symbol, cast(date as date) order by date) = 1
