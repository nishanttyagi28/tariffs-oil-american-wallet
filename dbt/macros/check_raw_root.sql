{% macro check_raw_root() -%}
    {#- Fail fast with a clear message when data/raw is not reachable (e.g. dbt run from the repo root). -#}
    {%- if execute -%}
    select case when (select count(*) from glob('{{ var("raw_root") }}/manifest.json')) = 0
        then error('data/raw not found at {{ var("raw_root") }} (cwd-relative). Run dbt from the dbt/ folder '
                   || '(cd dbt; dbt build --profiles-dir .) or set TRADEWAR_RAW to the absolute data/raw path.')
        else 1 end
    {%- else -%}
    select 1
    {%- endif %}
{%- endmacro %}
