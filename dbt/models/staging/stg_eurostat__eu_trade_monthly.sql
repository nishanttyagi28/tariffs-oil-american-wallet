select
    cast(period as date) as month_date,
    geo as reporter,
    partner,
    case stk_flow when 'EXP' then 'export' when 'IMP' then 'import' end as flow,
    cast(value_meur as double) as value_meur
from {{ raw('eurostat', 'eu27_trade_partner_monthly') }}
