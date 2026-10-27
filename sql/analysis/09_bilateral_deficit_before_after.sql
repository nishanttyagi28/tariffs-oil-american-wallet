-- US bilateral goods balance with each partner: avg monthly 2024 vs Apr-2025+, largest deficits.
select country_name, partner_group,
       round(balance_avg_before_musd, 0) as balance_avg_2024_musd,
       round(balance_avg_after_musd, 0) as balance_avg_after_musd,
       round(balance_change_musd, 0) as change_musd,
       case when balance_change_musd > 0 then 'deficit narrowed' else 'deficit widened' end as direction
from powerbi.mart_country_before_after
where entity_type in ('country', 'bloc')
order by balance_avg_before_musd asc
limit 20
