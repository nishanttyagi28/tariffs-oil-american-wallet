select cast(period as date) as month_date, cast(gscpi as double) as gscpi from {{ raw('gscpi', 'gscpi_monthly') }}
