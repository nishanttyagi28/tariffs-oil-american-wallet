-- CPI-U categories (BLS, NSA) with tariff-exposure grouping used for pass-through comparisons.
select
    series_id,
    category,
    exposure_group,
    case exposure_group
        when 'tariff_exposed_goods' then 'Tariff-exposed goods'
        when 'domestic_goods' then 'Domestic goods'
        when 'domestic_services' then 'Domestic services'
        when 'energy' then 'Energy'
        when 'energy_sensitive_services' then 'Energy-sensitive services'
        when 'food' then 'Food at home'
        else 'Aggregate'
    end            as exposure_label,
    is_headline
from {{ ref('cpi_category_map') }}