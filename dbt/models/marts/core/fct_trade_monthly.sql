-- US goods trade with each partner (Census, $M NSA), monthly, with YoY, share and rolling-12m metrics.
with t as (
    select month_date, country_iso3, coalesce(imports_musd, 0) as imports_musd, coalesce(exports_musd, 0) as exports_musd
    from {{ ref('int_trade__partner_monthly') }}
),
m as (
    select
        t.*,
        exports_musd - imports_musd                                   as balance_musd,
        exports_musd + imports_musd                                   as total_trade_musd,
        imports_musd / nullif(sum(imports_musd) over (partition by month_date), 0) as share_of_us_imports,
        exports_musd / nullif(sum(exports_musd) over (partition by month_date), 0) as share_of_us_exports,
        sum(imports_musd) over r12                                    as imports_r12m_musd,
        sum(exports_musd) over r12                                    as exports_r12m_musd,
        count(*) over r12                                             as months_in_r12m
    from t
    window r12 as (partition by country_iso3 order by month_date range between interval 11 month preceding and current row)
)
select
    m.*,
    ly.imports_musd                                                   as imports_musd_ly,
    ly.exports_musd                                                   as exports_musd_ly,
    m.imports_musd / nullif(ly.imports_musd, 0) - 1                   as imports_yoy_pct,
    m.exports_musd / nullif(ly.exports_musd, 0) - 1                   as exports_yoy_pct,
    m.balance_musd - (ly.exports_musd - ly.imports_musd)              as balance_yoy_change_musd
from m
left join t ly
       on ly.country_iso3 = m.country_iso3
      and ly.month_date = cast(m.month_date - interval 12 month as date)