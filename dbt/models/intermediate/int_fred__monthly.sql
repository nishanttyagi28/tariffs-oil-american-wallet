-- FRED series collapsed to monthly averages (daily/weekly series) or the monthly value itself.
select
    series_id,
    any_value(label)                                 as label,
    cast(date_trunc('month', obs_date) as date)      as month_date,
    avg(value)                                       as value,
    count(*)                                         as n_obs
from {{ ref('stg_fred__series') }}
where value is not null and frequency in ('D', 'W', 'M')
group by series_id, date_trunc('month', obs_date)