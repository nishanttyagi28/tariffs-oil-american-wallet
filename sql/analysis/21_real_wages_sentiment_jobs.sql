-- Household squeeze: wages vs prices (real wage YoY), sentiment, saving rate, unemployment, 2024 onward.
select month_date, round(100 * cpi_yoy_pct, 2) as cpi_yoy, round(100 * ahe_yoy_pct, 2) as wage_yoy, round(100 * real_wage_yoy_pct, 2) as real_wage_yoy,
       consumer_sentiment, personal_saving_rate_pct, unemployment_rate_pct, round(100 * retail_sales_yoy_pct, 2) as retail_sales_yoy,
       mortgage_30y_pct, round(gasoline_usd_gal, 2) as gasoline_usd_gal
from core.fct_macro_monthly
where month_date >= date '2024-01-01'
order by month_date
