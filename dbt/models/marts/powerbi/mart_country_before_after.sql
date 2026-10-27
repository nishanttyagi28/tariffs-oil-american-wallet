-- Before vs after per partner (+ EU-27 bloc): average monthly trade in 2024 vs Apr 2025 onward, like-for-like
-- YTD comparison (latest year's Jan..latest month vs same months of 2024), tariff peak/current, map coordinates.
with t as (
    select f.*, c.is_eu27 from {{ ref('fct_trade_monthly') }} f
    join {{ ref('dim_country') }} c using (country_iso3)
),
latest as (select max(month_date) as max_month from t),
unioned as (
    select month_date, country_iso3, imports_musd, exports_musd, balance_musd from t
    union all
    select month_date, 'EUU', sum(imports_musd), sum(exports_musd), sum(balance_musd) from t where is_eu27 group by month_date
),
agg as (
    select
        u.country_iso3,
        avg(case when u.month_date between date '{{ var("before_start") }}' and date '{{ var("before_end") }}' then imports_musd end) as imports_avg_before_musd,
        avg(case when u.month_date >= date '{{ var("after_start") }}' then imports_musd end)  as imports_avg_after_musd,
        avg(case when u.month_date between date '{{ var("before_start") }}' and date '{{ var("before_end") }}' then exports_musd end) as exports_avg_before_musd,
        avg(case when u.month_date >= date '{{ var("after_start") }}' then exports_musd end)  as exports_avg_after_musd,
        avg(case when u.month_date between date '{{ var("before_start") }}' and date '{{ var("before_end") }}' then balance_musd end) as balance_avg_before_musd,
        avg(case when u.month_date >= date '{{ var("after_start") }}' then balance_musd end)  as balance_avg_after_musd,
        sum(case when year(u.month_date) = year(l.max_month) then imports_musd end)           as imports_ytd_musd,
        sum(case when year(u.month_date) = 2024 and month(u.month_date) <= month(l.max_month) then imports_musd end) as imports_ytd_2024_musd,
        sum(case when year(u.month_date) = year(l.max_month) then exports_musd end)           as exports_ytd_musd,
        sum(case when year(u.month_date) = 2024 and month(u.month_date) <= month(l.max_month) then exports_musd end) as exports_ytd_2024_musd,
        sum(case when year(u.month_date) = 2024 then imports_musd end)                        as imports_2024_musd,
        sum(case when year(u.month_date) = 2025 then imports_musd end)                        as imports_2025_musd,
        any_value(l.max_month)                                                                as latest_month
    from unioned u cross join latest l
    group by u.country_iso3
),
tariff as (
    select country_iso3,
           max(max_rate_in_month_pct)                                                         as peak_statutory_rate_pct,
           arg_max(statutory_rate_pct, month_date)                                            as current_statutory_rate_pct
    from {{ ref('fct_tariff_rate_monthly') }} group by country_iso3
),
tot as (select sum(imports_avg_before_musd) as tb, sum(imports_avg_after_musd) as ta from agg where country_iso3 <> 'EUU')
select
    a.country_iso3,
    c.country_name,
    c.partner_group,
    c.region_wb,
    c.entity_type,
    c.is_focus,
    c.latitude,
    c.longitude,
    a.*  exclude (country_iso3),
    a.imports_avg_after_musd / nullif(a.imports_avg_before_musd, 0) - 1                   as imports_change_pct,
    a.exports_avg_after_musd / nullif(a.exports_avg_before_musd, 0) - 1                   as exports_change_pct,
    a.balance_avg_after_musd - a.balance_avg_before_musd                                  as balance_change_musd,
    a.imports_ytd_musd / nullif(a.imports_ytd_2024_musd, 0) - 1                           as imports_ytd_vs_2024_pct,
    a.exports_ytd_musd / nullif(a.exports_ytd_2024_musd, 0) - 1                           as exports_ytd_vs_2024_pct,
    a.imports_avg_before_musd / tot.tb                                                    as import_share_before,
    a.imports_avg_after_musd / tot.ta                                                     as import_share_after,
    (a.imports_avg_after_musd / tot.ta - a.imports_avg_before_musd / tot.tb) * 100        as import_share_change_pp,
    case when a.country_iso3 <> 'EUU' then rank() over (partition by a.country_iso3 = 'EUU' order by a.imports_avg_before_musd desc nulls last) end as import_rank_before,
    case when a.country_iso3 <> 'EUU' then rank() over (partition by a.country_iso3 = 'EUU' order by a.imports_avg_after_musd desc nulls last) end  as import_rank_after,
    coalesce(tr.peak_statutory_rate_pct, 0)                                               as peak_statutory_rate_pct,
    coalesce(tr.current_statutory_rate_pct, 0)                                            as current_statutory_rate_pct
from agg a
cross join tot
join {{ ref('dim_country') }} c using (country_iso3)
left join tariff tr using (country_iso3)
where a.imports_avg_before_musd is not null or a.imports_avg_after_musd is not null