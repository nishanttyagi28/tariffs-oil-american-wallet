-- Annualised volatility can never be negative.
select * from {{ ref('fct_market_daily') }} where vol_21d_ann < 0 or vol_63d_ann < 0
