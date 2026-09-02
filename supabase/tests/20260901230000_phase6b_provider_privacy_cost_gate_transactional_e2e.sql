begin;

do $$
declare
  v_luna jsonb;
  v_luna_replay jsonb;
  v_completed jsonb;
  v_completed_replay jsonb;
  v_terra jsonb;
  v_failed jsonb;
  v_cost record;
  v_budget ai_private.provider_test_budget%rowtype;
  v_gate jsonb;
  v_blocked boolean := false;
  v_start_completed_calls integer;
  v_start_consumed_eur_micros bigint;
begin
  v_gate := ai_private.phase6b_real_member_gate();
  if coalesce((v_gate->>'allowed')::boolean,true) or v_gate->>'deny_reason' <> 'real_member_provider_processing_blocked_phase6b' then
    raise exception 'phase6b real member gate did not fail closed';
  end if;

  select completed_calls, consumed_eur_micros
  into v_start_completed_calls, v_start_consumed_eur_micros
  from ai_private.provider_test_budget
  where policy_code='phase6b-staging-v1';

  select * into v_cost from ai_private.phase6b_estimate_test_cost('gpt-5.6-luna',120,20,80,1);
  if v_cost.usd_micros <> 117 or v_cost.eur_micros <> 147 then
    raise exception 'luna cost formula mismatch: %, %',v_cost.usd_micros,v_cost.eur_micros;
  end if;

  v_luna := public.fmz_phase6b_service_begin_synthetic_test(
    '60000000-0000-4000-8000-000000000001','luna_connectivity_v1',
    'connectivity_and_contract','luna',repeat('a',64)
  );
  if (v_luna->>'replay')::boolean or v_luna->>'model_id' <> 'gpt-5.6-luna' or v_luna->>'store' <> 'false' or v_luna->>'tools_allowed' <> 'false' then
    raise exception 'luna reservation contract failed';
  end if;
  v_luna_replay := public.fmz_phase6b_service_begin_synthetic_test(
    '60000000-0000-4000-8000-000000000001','luna_connectivity_v1',
    'connectivity_and_contract','luna',repeat('a',64)
  );
  if not (v_luna_replay->>'replay')::boolean or v_luna_replay->>'run_id' <> v_luna->>'run_id' then
    raise exception 'luna reservation replay failed';
  end if;
  begin
    perform public.fmz_phase6b_service_begin_synthetic_test(
      '60000000-0000-4000-8000-000000000001','luna_connectivity_v1',
      'connectivity_and_contract','luna',repeat('b',64)
    );
  exception when unique_violation then
    v_blocked := true;
  end;
  if not v_blocked then raise exception 'request replay conflict was accepted'; end if;

  v_completed := public.fmz_phase6b_service_complete_synthetic_test(
    (v_luna->>'run_id')::uuid,1,120,20,80,repeat('c',64),repeat('d',64)
  );
  if v_completed->>'status' <> 'completed' or (v_completed->>'actual_eur_micros')::bigint <> 147 then
    raise exception 'completion accounting failed';
  end if;
  v_completed_replay := public.fmz_phase6b_service_complete_synthetic_test(
    (v_luna->>'run_id')::uuid,1,120,20,80,repeat('c',64),repeat('d',64)
  );
  if not (v_completed_replay->>'replay')::boolean then raise exception 'completion replay failed'; end if;

  v_terra := public.fmz_phase6b_service_begin_synthetic_test(
    '60000000-0000-4000-8000-000000000002','terra_structured_v1',
    'complex_route_contract','terra',repeat('e',64)
  );
  v_failed := public.fmz_phase6b_service_fail_synthetic_test(
    (v_terra->>'run_id')::uuid,1,'provider_timeout',true
  );
  if v_failed->>'status' <> 'failed' or (v_failed->>'charged_eur_micros')::bigint <= 0 then
    raise exception 'conservative failed-call accounting failed';
  end if;

  select * into v_budget from ai_private.provider_test_budget where policy_code='phase6b-staging-v1';
  if v_budget.reserved_calls <> 0 or v_budget.reserved_eur_micros <> 0
     or v_budget.completed_calls <> v_start_completed_calls + 2
     or v_budget.consumed_eur_micros <= v_start_consumed_eur_micros + 147
     or v_budget.consumed_eur_micros > v_budget.max_total_eur_micros then
    raise exception 'budget reconciliation state invalid';
  end if;

  update ai_private.provider_test_budget
  set completed_calls=max_external_calls
  where policy_code='phase6b-staging-v1';
  v_blocked := false;
  begin
    perform public.fmz_phase6b_service_begin_synthetic_test(
      '60000000-0000-4000-8000-000000000003','luna_connectivity_v1',
      'connectivity_and_contract','luna',repeat('f',64)
    );
  exception when insufficient_privilege then
    v_blocked := true;
  end;
  if not v_blocked then raise exception 'external-call cap was bypassed'; end if;

  update ai_private.provider_test_budget
  set completed_calls=0,consumed_eur_micros=max_total_eur_micros
  where policy_code='phase6b-staging-v1';
  v_blocked := false;
  begin
    perform public.fmz_phase6b_service_begin_synthetic_test(
      '60000000-0000-4000-8000-000000000004','luna_connectivity_v1',
      'connectivity_and_contract','luna',repeat('0',64)
    );
  exception when insufficient_privilege then
    v_blocked := true;
  end;
  if not v_blocked then raise exception 'EUR 5 cap was bypassed'; end if;
end;
$$;

select jsonb_build_object(
  'overall_pass',true,
  'synthetic_provider_calls',0,
  'external_ai_cost_eur',0,
  'real_member_processing',false,
  'fixtures_persisted',false
) as test_result;

rollback;
