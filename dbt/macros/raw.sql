{% macro raw(source, dataset) -%}
    read_parquet('{{ var("raw_root") }}/{{ source }}/{{ dataset }}.parquet')
{%- endmacro %}
