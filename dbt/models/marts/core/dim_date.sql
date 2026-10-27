-- Daily calendar 2015-2026 with trade-war and Iran-war phase labels and before/after flags.
with days as (
    select cast(d as date) as date_day
    from generate_series(date '2015-01-01', date '2026-12-31', interval 1 day) as g(d)
),
phases as (select * from {{ ref('event_phases') }})
select
    days.date_day,
    cast(date_trunc('month', days.date_day) as date)                  as month_date,
    year(days.date_day)                                               as year,
    quarter(days.date_day)                                            as quarter,
    month(days.date_day)                                              as month,
    strftime(days.date_day, '%b %Y')                                  as month_label,
    strftime(days.date_day, '%Y-%m')                                  as year_month,
    isodow(days.date_day)                                             as iso_dow,
    isodow(days.date_day) >= 6                                        as is_weekend,
    days.date_day = cast(date_trunc('month', days.date_day) as date)  as is_month_start,
    tp.phase_code                                                     as trade_phase_code,
    tp.phase_order                                                    as trade_phase_order,
    tp.phase_name                                                     as trade_phase,
    wp.phase_code                                                     as war_phase_code,
    wp.phase_order                                                    as war_phase_order,
    wp.phase_name                                                     as war_phase,
    case
        when days.date_day between date '{{ var("before_start") }}' and date '{{ var("before_end") }}' then 'Before (2024)'
        when days.date_day >= date '{{ var("after_start") }}' then 'After (Apr 2025+)'
        else 'Other'
    end                                                               as before_after,
    days.date_day >= date '{{ var("war_start") }}'                    as is_war_period
from days
left join phases tp on tp.phase_type = 'trade' and days.date_day between tp.start_date and tp.end_date
left join phases wp on wp.phase_type = 'war'   and days.date_day between wp.start_date and wp.end_date