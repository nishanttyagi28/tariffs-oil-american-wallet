-- Household prices: tariff-exposed goods vs domestic services inflation (YoY) and the gap, by month.
select month_date, trade_phase, war_phase,
       round(100 * cpi_headline_yoy_pct, 2) as headline_yoy, round(100 * cpi_core_goods_yoy_pct, 2) as core_goods_yoy,
       round(100 * tariff_exposed_goods_yoy_pct, 2) as tariff_goods_yoy, round(100 * domestic_services_yoy_pct, 2) as services_yoy,
       round(tariff_goods_minus_services_pp, 2) as goods_minus_services_pp
from powerbi.mart_household_impact
where month_date >= date '2024-01-01'
order by month_date
