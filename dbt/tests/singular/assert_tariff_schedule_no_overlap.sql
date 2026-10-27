-- A country's headline tariff schedule rows must not overlap in time.
select a.country_iso3, a.start_date, b.start_date as overlapping_start
from {{ ref('tariff_headline_schedule') }} a
join {{ ref('tariff_headline_schedule') }} b
  on a.country_iso3 = b.country_iso3 and a.start_date < b.start_date
 and b.start_date <= coalesce(a.end_date, date '2099-12-31')
