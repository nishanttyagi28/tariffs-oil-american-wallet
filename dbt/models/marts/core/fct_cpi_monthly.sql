-- CPI-U by category (BLS, NSA): YoY, MoM, and index rebased to Jan 2025 = 100 (tariff-era start).
with c as (
    select series_id, month_date, index_value
    from {{ ref('stg_bls__cpi') }}
    qualify row_number() over (partition by series_id, month_date order by index_value) = 1
),
jan25 as (select series_id, index_value as base_jan2025 from c where month_date = date '2025-01-01'),
avg24 as (select series_id, avg(index_value) as base_2024 from c where year(month_date) = 2024 group by series_id)
select
    c.series_id,
    c.month_date,
    c.index_value,
    c.index_value / nullif(ly.index_value, 0) - 1                     as yoy_pct,
    c.index_value / nullif(lag(c.index_value) over w, 0) - 1          as mom_pct,
    100 * c.index_value / nullif(jan25.base_jan2025, 0)               as index_jan2025_100,
    c.index_value / nullif(jan25.base_jan2025, 0) - 1                 as change_since_jan2025_pct,
    c.index_value / nullif(avg24.base_2024, 0) - 1                    as change_vs_2024_avg_pct
from c
left join c ly on ly.series_id = c.series_id and ly.month_date = cast(c.month_date - interval 12 month as date)
left join jan25 on jan25.series_id = c.series_id
left join avg24 on avg24.series_id = c.series_id
window w as (partition by c.series_id order by c.month_date)