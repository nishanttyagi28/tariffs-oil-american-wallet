-- Market instruments (Yahoo Finance) with region for the global-markets pages.
with px as (
    select symbol, min(trade_date) as first_date, max(trade_date) as last_date, count(*) as n_days
    from {{ ref('stg_yahoo__prices') }} group by symbol
)
select
    i.symbol,
    i.name                                          as instrument_name,
    i.asset_class,
    i.country_iso3,
    i.currency,
    case
        when i.country_iso3 in ('USA') then 'United States'
        when i.country_iso3 in ('DEU', 'EUU', 'GBR') then 'Europe'
        when i.country_iso3 in ('IND') then 'India'
        when i.country_iso3 in ('CHN', 'HKG') then 'China'
        when i.country_iso3 in ('JPN') then 'Japan'
        when i.country_iso3 in ('CAN', 'MEX') then 'North America ex-US'
        else 'Global'
    end                                             as market_region,
    -- FX quotes are local currency per USD except EURUSD (USD per EUR)
    case when i.asset_class = 'fx' and i.symbol <> 'EURUSD=X' and i.symbol <> 'DX-Y.NYB' then true else false end
                                                    as is_usd_base_fx,
    px.first_date,
    px.last_date,
    px.n_days
from {{ ref('stg_yahoo__instruments') }} i
left join px using (symbol)