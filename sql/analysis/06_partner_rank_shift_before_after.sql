-- Biggest winners/losers in US import share: 2024 baseline vs Apr-2025+ (mart_country_before_after).
select country_name, partner_group, import_rank_before, import_rank_after,
       import_rank_before - import_rank_after as rank_gain,
       round(100 * import_share_before, 2) as share_before_pct,
       round(100 * import_share_after, 2) as share_after_pct,
       round(import_share_change_pp, 2) as share_change_pp,
       round(100 * imports_change_pct, 1) as imports_change_pct,
       peak_statutory_rate_pct, current_statutory_rate_pct
from powerbi.mart_country_before_after
where entity_type = 'country' and import_rank_before <= 30
qualify row_number() over (order by abs(import_share_change_pp) desc) <= 20
order by import_share_change_pp desc
