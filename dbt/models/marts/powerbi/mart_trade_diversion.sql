-- Trade diversion: monthly share of US goods imports by partner group vs the 2024 average share,
-- and the implied $ diverted (share change x total US imports).
with t as (
    select f.month_date, c.partner_group, sum(f.imports_musd) as imports_musd, sum(f.exports_musd) as exports_musd
    from {{ ref('fct_trade_monthly') }} f join {{ ref('dim_country') }} c using (country_iso3)
    where f.month_date >= date '2023-01-01'
    group by all
),
s as (
    select t.*,
           sum(imports_musd) over (partition by month_date)                      as us_imports_musd,
           imports_musd / sum(imports_musd) over (partition by month_date)       as import_share
    from t
),
b as (
    select partner_group, sum(imports_musd) / sum(sum(imports_musd)) over () as import_share_2024
    from t where year(month_date) = 2024 group by partner_group
)
select
    s.month_date,
    s.partner_group,
    s.imports_musd,
    s.exports_musd,
    s.exports_musd - s.imports_musd                                       as balance_musd,
    s.us_imports_musd,
    s.import_share,
    b.import_share_2024,
    (s.import_share - b.import_share_2024) * 100                          as share_change_pp,
    (s.import_share - b.import_share_2024) * s.us_imports_musd            as diverted_imports_musd,
    sum(s.imports_musd) over (partition by s.partner_group order by s.month_date
                              range between interval 11 month preceding and current row) as imports_r12m_musd,
    rank() over (partition by s.month_date order by s.imports_musd desc)  as rank_in_month
from s
left join b using (partner_group)