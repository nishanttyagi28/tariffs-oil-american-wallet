-- US goods trade by partner (ISO3), monthly, $ millions NSA. Census aggregates (codes < 1000) are excluded,
-- so summing partners reproduces the Census "World" total (checked in tests/assert_census_partner_sum_matches_world.sql).
with trade as (
    select * from {{ ref('stg_census__trade_monthly') }} where not is_aggregate
),
xw as (
    select * from {{ ref('stg_crosswalk__census_country') }}
)
select
    trade.month_date,
    coalesce(xw.iso3,
             case trade.cty_code when '4803' then 'XKX' when '5082' then 'PSE' when '5083' then 'PSE' end,
             'C' || trade.cty_code)                                    as country_iso3,
    sum(case when trade.flow = 'import' then trade.value_musd end)     as imports_musd,
    sum(case when trade.flow = 'export' then trade.value_musd end)     as exports_musd
from trade
left join xw on xw.cty_code = trade.cty_code
group by all