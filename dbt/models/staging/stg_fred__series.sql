select series_id, label, frequency, cast(period as date) as obs_date, cast(value as double) as value
from {{ raw('fred', 'fred_series') }}
