-- The "Before" label must be exactly calendar 2024.
select * from {{ ref('dim_date') }}
where (before_after = 'Before (2024)') <> (year = 2024)
