-- "China+1": monthly import share of China vs Vietnam, Taiwan, Mexico, India (PIVOT), 2024 onward.
pivot (
  select month_date, country_iso3, round(100 * share_of_us_imports, 2) as share_pct
  from core.fct_trade_monthly
  where country_iso3 in ('CHN', 'VNM', 'TWN', 'MEX', 'IND') and month_date >= date '2024-01-01'
) on country_iso3 using first(share_pct)
order by month_date
