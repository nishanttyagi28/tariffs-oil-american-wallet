-- Average YoY inflation by CPI exposure group and tariff/war phase (household lens).
select c.exposure_group, d.trade_phase_order, d.trade_phase, d.war_phase,
       round(100 * avg(f.yoy_pct), 2) as avg_yoy_pct, count(*) as obs
from core.fct_cpi_monthly f
join core.dim_cpi_category c using (series_id)
join core.dim_date d on d.date_day = f.month_date
where f.month_date >= date '2024-01-01' and not c.is_headline
group by all order by c.exposure_group, d.trade_phase_order, d.war_phase
