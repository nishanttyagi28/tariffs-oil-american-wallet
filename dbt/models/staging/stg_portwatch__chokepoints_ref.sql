select
    portid                         as chokepoint_id,
    portname                       as chokepoint_name,
    cast(lat as double)            as latitude,
    cast(lon as double)            as longitude
from {{ raw('portwatch', 'chokepoints_ref') }}
where portid is not null
qualify row_number() over (partition by portid order by portname) = 1