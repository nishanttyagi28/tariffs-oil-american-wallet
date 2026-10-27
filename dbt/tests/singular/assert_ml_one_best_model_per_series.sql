-- Exactly one best model per trade series and metric.
select series_id, metric, count(*) as n
from {{ source('ml', 'ml_model_metrics') }}
where task = 'trade_counterfactual' and is_best
group by 1, 2 having count(*) <> 1