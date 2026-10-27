-- MTS reports amounts in dollars; convert to $ millions. Refunds surge after the Feb-2026 IEEPA ruling.
select
    cast(date_trunc('month', record_date) as date)     as month_date,
    cast(record_date as date)                          as record_date,
    current_month_gross_rcpt_amt / 1e6                 as gross_receipts_musd,
    current_month_refund_amt / 1e6                     as refunds_musd,
    current_month_net_rcpt_amt / 1e6                   as net_receipts_musd
from {{ raw('treasury', 'mts_customs_duties_monthly') }}
