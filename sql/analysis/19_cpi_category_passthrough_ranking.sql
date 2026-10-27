-- Pass-through ranking: annualised inflation per CPI category before (Dec-2022 -> Dec-2024) vs after (Dec-2024 -> latest).
with p as (
  select series_id,
         max(index_value) filter (where month_date = date '2022-12-01') as i_2022,
         max(index_value) filter (where month_date = date '2024-12-01') as i_2024,
         arg_max(index_value, month_date) as i_last, max(month_date) as last_month
  from core.fct_cpi_monthly group by 1
)
select c.category, c.exposure_group,
       round(100 * (power(i_2024 / i_2022, 0.5) - 1), 2) as ann_infl_2023_24_pct,
       round(100 * (power(i_last / i_2024, 12.0 / date_diff('month', date '2024-12-01', last_month)) - 1), 2) as ann_infl_since_2025_pct,
       round(100 * (power(i_last / i_2024, 12.0 / date_diff('month', date '2024-12-01', last_month)) - 1)
             - 100 * (power(i_2024 / i_2022, 0.5) - 1), 2) as acceleration_pp
from p join core.dim_cpi_category c using (series_id)
order by acceleration_pp desc
