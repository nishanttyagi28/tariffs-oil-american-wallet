select cast(date as date) as obs_date, benchmark, cast(price_usd_bbl as double) as price_usd_bbl
from {{ raw('eia', 'crude_spot_daily') }}
where price_usd_bbl > 0
