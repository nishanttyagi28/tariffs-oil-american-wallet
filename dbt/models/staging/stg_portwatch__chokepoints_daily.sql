-- IMF PortWatch: daily vessel transits through 28 maritime chokepoints (AIS satellite signals).
select
    cast(date as date)              as obs_date,
    portid                          as chokepoint_id,
    portname                        as chokepoint_name,
    cast(n_total as integer)        as n_total,
    cast(n_tanker as integer)       as n_tanker,
    cast(n_container as integer)    as n_container,
    cast(n_dry_bulk as integer)     as n_dry_bulk,
    cast(n_cargo as integer)        as n_cargo,
    cast(capacity as double)        as capacity_dwt,
    cast(capacity_tanker as double) as capacity_tanker_dwt
from {{ raw('portwatch', 'chokepoints_daily') }}
where date is not null
qualify row_number() over (partition by portid, cast(date as date) order by n_total desc) = 1