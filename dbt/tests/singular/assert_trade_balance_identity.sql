-- Balance = exports - imports; total trade = exports + imports.
select * from {{ ref('fct_trade_monthly') }}
where abs(balance_musd - (exports_musd - imports_musd)) > 0.01
   or abs(total_trade_musd - (exports_musd + imports_musd)) > 0.01
