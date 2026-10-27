select symbol, name, asset_class, country_iso3, currency from {{ raw('yahoo', 'instruments') }}
