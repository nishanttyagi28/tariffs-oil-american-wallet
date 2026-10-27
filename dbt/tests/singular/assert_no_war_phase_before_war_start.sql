-- Iran-war phases may only start on/after the war start date (28 Feb 2026).
select * from {{ ref('dim_date') }}
where is_war_period and date_day < date '{{ var("war_start") }}'
