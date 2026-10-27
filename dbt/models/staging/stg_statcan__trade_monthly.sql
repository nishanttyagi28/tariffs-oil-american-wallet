-- Statistics Canada 12-10-0011-01: Canada's merchandise trade with principal partners (customs basis, NSA, C$ millions).
-- Gives the Canadian side of the US-Canada relationship (mirror of US Census data).
select
    cast(period as date)                            as month_date,
    lower(trade)                                    as flow,           -- import / export
    replace(principal_trading_partners, 'T' || chr(65533) || 'rkiye', 'Turkiye') as partner,
    cast(value as double)                           as value_mcad
from {{ raw('statcan', 'trade_principal_partners_monthly') }}
where basis = 'Customs'
  and seasonal_adjustment = 'Unadjusted'
  and lower(trade) in ('import', 'export')
  and value is not null