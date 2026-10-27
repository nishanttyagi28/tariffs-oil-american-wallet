-- The calendar must have no gaps.
select date_day from (
  select date_day, lead(date_day) over (order by date_day) as nxt from {{ ref('dim_date') }}
) where nxt is not null and nxt <> date_day + interval 1 day
