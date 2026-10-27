-- Census published totals: World NSA (0015) and European Union (0003), used for reconciliation tests.
select
    month_date,
    case cty_code when '0015' then 'WORLD' when '0003' then 'EU' end as aggregate_code,
    sum(case when flow = 'import' then value_musd end) as imports_musd,
    sum(case when flow = 'export' then value_musd end) as exports_musd
from {{ ref('stg_census__trade_monthly') }}
where cty_code in ('0015', '0003')
group by all