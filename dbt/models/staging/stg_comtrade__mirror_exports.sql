select reporter_code, reporter, cast(period as date) as month_date, cast(value_usd as double) as value_usd
from {{ raw('comtrade', 'mirror_exports_to_us_monthly') }}
where value_usd is not null
