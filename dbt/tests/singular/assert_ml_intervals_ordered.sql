-- ML prediction intervals must nest: lo95 <= lo80 <= point <= hi80 <= hi95.
select 'trade' as src, series_id as id, month_date from {{ source('ml', 'ml_trade_counterfactual') }}
where is_post and not (cf_lo95 <= cf_lo80 + 1e-9 and cf_lo80 <= counterfactual_musd + 1e-9
                       and counterfactual_musd <= cf_hi80 + 1e-9 and cf_hi80 <= cf_hi95 + 1e-9)
union all
select 'forecast', target, month_date from {{ source('ml', 'ml_forecasts') }}
where kind like 'forecast%' and not (lo95 <= lo80 + 1e-9 and lo80 <= value + 1e-9 and value <= hi80 + 1e-9 and hi80 <= hi95 + 1e-9)