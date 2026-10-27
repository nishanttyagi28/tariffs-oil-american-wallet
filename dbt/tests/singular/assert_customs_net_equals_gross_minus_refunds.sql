-- Net customs receipts must equal gross minus refunds (within $1m rounding).
select * from {{ ref('fct_customs_revenue_monthly') }}
where abs(net_receipts_musd - (gross_receipts_musd - refunds_musd)) > 1
