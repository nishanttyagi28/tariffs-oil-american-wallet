{% macro generate_schema_name(custom_schema_name, node) -%}
    {#- Use clean schema names (staging, core, powerbi...) instead of main_staging -#}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}
