select cty_code, census_name, iso2, iso3, ne_name, continent, region_un, subregion, region_wb, income_grp,
       cast(latitude as double) as latitude, cast(longitude as double) as longitude
from {{ raw('crosswalk', 'census_country_iso') }}
