select series_id, category, cast(period as date) as month_date, cast(index_value as double) as index_value
from {{ raw('bls', 'cpi_categories_monthly') }}
