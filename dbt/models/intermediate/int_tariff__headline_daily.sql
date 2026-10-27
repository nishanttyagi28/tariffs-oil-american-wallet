-- Daily statutory *additional* headline tariff (pct points on top of MFN) per schedule key
-- (CHN, CAN, MEX, IND, EUU, WLD) from the hand-verified seed. Days with no schedule row = 0.
with keys as (
    select distinct country_iso3 as schedule_key from {{ ref('tariff_headline_schedule') }}
),
days as (
    select cast(d as date) as obs_date
    from generate_series(date '2024-01-01', current_date, interval 1 day) as g(d)
)
select
    days.obs_date,
    keys.schedule_key,
    coalesce(max(s.headline_rate_pct), 0) as headline_rate_pct,
    max(s.basis)                          as basis,
    coalesce(bool_and(s.verified), true)  as verified
from days
cross join keys
left join {{ ref('tariff_headline_schedule') }} s
       on s.country_iso3 = keys.schedule_key
      and days.obs_date between s.start_date and s.end_date
group by all