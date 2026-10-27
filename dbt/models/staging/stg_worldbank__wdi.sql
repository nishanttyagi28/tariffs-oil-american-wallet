select iso3, country, indicator, indicator_name, year, cast(value as double) as value
from {{ raw('worldbank', 'wdi_annual') }}
where value is not null and iso3 is not null and iso3 <> ''
