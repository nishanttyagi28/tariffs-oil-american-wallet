-- Event-window base date must precede the window end date, and base close must be positive.
select * from {{ ref('mart_market_event_window') }}
where base_date >= end_date or base_close <= 0
