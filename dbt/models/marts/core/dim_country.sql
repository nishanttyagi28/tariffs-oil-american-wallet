-- One row per partner (ISO3) plus bloc rows (EUU = EU-27, ALL = all partners / US total).
-- Map coordinates: Natural Earth label points, falling back to hand-entered capitals for micro-states.
with ne as (select * from {{ ref('stg_naturalearth__countries') }}),
xw as (
    select iso3, any_value(census_name) as census_name, any_value(latitude) as latitude, any_value(longitude) as longitude,
           any_value(continent) as continent, any_value(region_wb) as region_wb, any_value(subregion) as subregion
    from {{ ref('stg_crosswalk__census_country') }} where iso3 is not null group by iso3
),
traded as (select distinct country_iso3 as iso3 from {{ ref('int_trade__partner_monthly') }}),
eu as (select iso3 from {{ ref('eu27_members') }}),
schedule as (select distinct country_iso3 as iso3 from {{ ref('tariff_headline_schedule') }}),
base as (
    select
        coalesce(ne.iso3, xw.iso3, traded.iso3)                          as country_iso3,
        coalesce(xw.census_name, ne.country_name, traded.iso3)           as country_name,
        coalesce(ne.continent, xw.continent, 'Other')                    as continent,
        coalesce(ne.region_wb, xw.region_wb, 'Other')                    as region_wb,
        coalesce(ne.subregion, xw.subregion)                             as subregion,
        ne.income_grp                                                    as income_group,
        ne.pop_est,
        ne.gdp_md_usd,
        coalesce(ne.latitude, xw.latitude)                               as latitude,
        coalesce(ne.longitude, xw.longitude)                             as longitude,
        traded.iso3 is not null                                          as is_us_trade_partner
    from ne
    full outer join xw on xw.iso3 = ne.iso3
    full outer join traded on traded.iso3 = coalesce(ne.iso3, xw.iso3)
),
countries as (
    select
        b.*,
        eu.iso3 is not null                                              as is_eu27,
        case
            when b.country_iso3 = 'CHN' then 'China'
            when b.country_iso3 = 'HKG' then 'Hong Kong'
            when b.country_iso3 = 'CAN' then 'Canada'
            when b.country_iso3 = 'MEX' then 'Mexico'
            when b.country_iso3 = 'IND' then 'India'
            when b.country_iso3 = 'JPN' then 'Japan'
            when b.country_iso3 = 'VNM' then 'Vietnam'
            when b.country_iso3 = 'TWN' then 'Taiwan'
            when b.country_iso3 = 'KOR' then 'South Korea'
            when b.country_iso3 = 'GBR' then 'United Kingdom'
            when b.country_iso3 = 'CHE' then 'Switzerland'
            when eu.iso3 is not null then 'European Union'
            when b.region_wb = 'East Asia & Pacific' or b.region_wb = 'South Asia' then 'Rest of Asia-Pacific'
            when b.region_wb = 'Latin America & Caribbean' then 'Rest of Americas'
            else 'Rest of World'
        end                                                              as partner_group,
        b.country_iso3 in ('CHN', 'CAN', 'MEX', 'IND', 'JPN') or eu.iso3 is not null as is_focus,
        case
            when schedule.iso3 is not null then b.country_iso3
            when eu.iso3 is not null then 'EUU'
            else 'WLD'
        end                                                              as tariff_schedule_key,
        'country'                                                        as entity_type
    from base b
    left join eu on eu.iso3 = b.country_iso3
    left join schedule on schedule.iso3 = b.country_iso3
    where b.country_iso3 is not null
)
select * from countries
union all
select 'EUU', 'European Union (EU-27)', 'Europe', 'Europe & Central Asia', 'European Union', 'High income', null, null,
       50.11, 9.25, true, false, 'European Union', true, 'EUU', 'bloc'
union all
select 'ALL', 'All partners (US total)', 'World', 'World', 'World', null, null, null,
       null, null, true, false, 'All partners', false, 'WLD', 'bloc'