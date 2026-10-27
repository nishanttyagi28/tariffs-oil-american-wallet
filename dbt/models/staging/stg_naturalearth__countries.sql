select iso3, name as country_name, name_long, continent, region_un, subregion, region_wb, economy, income_grp,
       cast(pop_est as double) as pop_est, cast(gdp_md as double) as gdp_md_usd,
       cast(label_y as double) as latitude, cast(label_x as double) as longitude
from {{ raw('naturalearth', 'countries') }}
where iso3 is not null and iso3 <> '-99'
qualify row_number() over (partition by iso3 order by pop_est desc) = 1
