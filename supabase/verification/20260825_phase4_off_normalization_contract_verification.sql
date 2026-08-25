-- FitMetZorge Phase 4 Slice 4F PostgreSQL-authoritative normalization contract
-- Read-only fixture verifier. The public PostgreSQL function is the authority.

with
cases(case_id, input_value, expected_value) as (
  values
    ('trademark', 'A™ B', 'a b'),
    ('ordinal', 'Penne Nº 41', 'penne nº 41'),
    ('subscript', 'CO₂ test', 'co test'),
    ('decomposed_accent', U&'Mango dri\0302nk', 'mango dri nk'),
    ('precomposed_accent', 'Mango drînk', 'mango drînk'),
    ('thai', 'ผงทำหมูแดง', 'ผงทำหม แดง'),
    ('korean', 'ㅋㄴ타블러ㅣ', 'ㅋㄴ타블러ㅣ'),
    ('punctuation', 'Red-Bull / Zero', 'red bull zero'),
    ('multiple_whitespace', E'Red   Bull\tZero', 'red bull zero'),
    ('leading_trailing', '  Red Bull  ', 'red bull'),
    ('mixed_unicode_ascii', 'Barkleys™ Nº5 CO₂', 'barkleys nº5 co'),
    ('brand', 'Albert Heijn, AH Biologisch', 'albert heijn ah biologisch'),
    ('product_name', 'Ben & Jerry''s Glace 465ml', 'ben jerry s glace 465ml')
),
evaluated as (
  select
    case_id,
    expected_value,
    public.fmz_phase4_normalize_catalog_text(input_value) as actual_value
  from cases
),
result as (
  select jsonb_build_object(
    'overall_pass', bool_and(actual_value = expected_value),
    'pass_count', count(*) filter (where actual_value = expected_value),
    'fail_count', count(*) filter (where actual_value is distinct from expected_value),
    'checks', jsonb_agg(
      jsonb_build_object(
        'check', case_id,
        'pass', actual_value = expected_value,
        'expected_utf8_hex', encode(convert_to(expected_value, 'UTF8'), 'hex'),
        'actual_utf8_hex', encode(convert_to(actual_value, 'UTF8'), 'hex')
      )
      order by case_id
    )
  ) as verification_result
  from evaluated
)
select verification_result from result;
