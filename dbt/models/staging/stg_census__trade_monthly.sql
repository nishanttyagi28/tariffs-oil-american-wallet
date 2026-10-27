-- US goods trade by Census partner code, monthly, millions USD (NSA)
select
    cast(period as date)              as month_date,
    cast(year as integer)             as year,
    cast(month as integer)            as month,
    cty_code,
    trim(cty_name)                    as cty_name,
    flow,
    cast(value_musd as double)        as value_musd,
    -- Census aggregates (World, EU, regions, groups) use codes below 1000
    try_cast(cty_code as integer) < 1000 as is_aggregate
from {{ raw('census_country', 'trade_by_country_monthly') }}
