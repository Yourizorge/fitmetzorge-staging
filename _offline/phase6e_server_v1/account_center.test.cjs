'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('./account_center.cjs');
const UI = require('./account_center.js');
const P = require('./access_policy.cjs');
const preferences = require('./presentation.cjs').preferences;
const start = Date.UTC(2026, 0, 1);
const source = () => ({id:'explicit-synthetic-test-source',version:7,synthetic_only:true,verified:true,
  grants:[{id:'existing-trial',kind:'trial',tier:'ai',start,end:start+30*P.DAY,revoked:false}]});
const view = (role='member',workspace='workspace-a') => ({workspace,role,version:2,
  capabilities:{full_day21:false},state:{route:'A',active:{version:1,training:{sessions:[]}},review:null}});

test('missing source stays unknown, not Free, irrespective of browser clock', () => {
  for (const value of [null, undefined]) {
    assert.deepEqual(A.access(value, start), {status:'source_missing',read_only:true});
    assert.equal(UI.accessStatus(value), 'source_missing');
    for(let language=0;language<3;language++) {
      const html=UI.accessPanel(A.access(value,start),language);
      assert.match(html,/data-access-status="source_missing"/);
      assert.doesNotMatch(html,/<dd>|<button|Free|Pro/);
    }
  }
});

test('unverified, real, malformed or conflicting sources fail closed', () => {
  const s=source();
  for(const input of [{...s,verified:false},{...s,synthetic_only:false},{...s,version:0},{...s,grants:[] ,id:''},
    {...s,grants:[{...s.grants[0],end:start+7*P.DAY}]}, {...s,grants:[...s.grants,{...s.grants[0],id:'second-trial'}]}]) {
    assert.deepEqual(A.access(input,start),{status:'source_invalid',read_only:true});
  }
  assert.equal(A.access(s,NaN).status,'source_invalid');
  assert.equal(A.access(s,undefined).status,'source_invalid');
});

test('projection delegates exact boundaries and fallback to the unchanged policy', () => {
  const s=source();
  for(const now of [start-1,start,start+23*P.DAY,start+29*P.DAY,start+30*P.DAY-1,start+30*P.DAY]) {
    const result=A.access(s,now);
    assert.deepEqual(result.policy,P.view(s,now));
    assert.equal(result.trial.fallback.tier,P.view(s,s.grants[0].end).tier);
    assert.equal(result.evaluated_at,now);
    assert.equal(UI.accessStatus(result),'verified_synthetic');
  }
  assert.equal(A.access(s,start-1).trial.status,'scheduled');
  assert.equal(A.access(s,start).trial.status,'active');
  assert.equal(A.access(s,start+30*P.DAY).trial.status,'expired');
  s.grants.push({id:'existing-pro',kind:'paid',tier:'pro',start,end:start+60*P.DAY,revoked:false});
  assert.equal(A.access(s,start).trial.fallback.tier,'pro');
  s.grants[0].revoked=true;
  assert.equal(A.access(s,start).trial.status,'revoked');
  assert.equal(A.access(s,start).trial.fallback,null);
  assert.deepEqual(A.access(s,start).policy.notices,[]);
});

test('explicit verified empty source can show Free; no missing-source inference', () => {
  const result=A.access({...source(),grants:[]},start);
  assert.equal(result.policy.tier,'free');assert.equal(result.trial,null);
  assert.match(UI.accessPanel(result,1),/<dd>Free<\/dd>/);
});

test('projection is immutable and contains no activation capability', () => {
  const s=source(),before=structuredClone(s);
  Object.freeze(s.grants[0]);Object.freeze(s.grants);Object.freeze(s);
  const result=A.access(s,start);
  assert.deepEqual(s,before);
  for(const key of ['trial_creation_allowed','external_ai_enabled','payment_action_allowed','automatic_renewal']) assert.equal(result.policy[key],false);
  assert.equal(result.policy.retained_history,true);
  result.source.id='changed';assert.equal(s.id,before.id);
});

test('all account strings have distinct nonempty NL EN DE entries', () => {
  for(const [key,value] of Object.entries(UI.words)) {
    assert.equal(value.length,3,key);assert.ok(value.every(x=>typeof x==='string'&&x.trim()),key);
  }
});

test('projection renders source times in UTC, escapes source IDs, and never offers a grant action', () => {
  const s=source();s.id='<img src=x onerror=alert(1)>';
  const result=A.access(s,start+29*P.DAY);
  for(let language=0;language<3;language++) {
    const html=UI.accessPanel(result,language);
    assert.match(html,/UTC/);assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<img|<button|<input/);
    assert.ok(html.includes(UI.words.one_day[language]));
    assert.ok(html.includes(UI.words.noticeRule[language]));
  }
});

test('browser fails closed for incompatible projections', () => {
  const s=A.access(source(),start);
  for(const value of [{}, {...s,read_only:false},{...s,source:{id:'x',version:8}},
    {...s,policy:{...s.policy,tier:'premium'}},{...s,policy:{...s.policy,external_ai_enabled:true}},
    {...s,trial:{...s.trial,status:'made-up'}}]) assert.equal(UI.accessStatus(value),'source_invalid');
});

test('trainer directory uses minimal view and never renders member-only data', () => {
  const trainer=view('trainer'),member={...view('member','private-member'),state:{nutrition:'PRIVATE FOOD',preferences:'PRIVATE PREFS'}};
  const html=UI.directory([trainer,member],trainer,1,k=>k,true);
  assert.match(html,/workspace-a/);assert.doesNotMatch(html,/private-member|PRIVATE|data-action|data-preferences/);
  assert.deepEqual(UI.tabs(trainer),['clients','today','review','account']);
  assert.match(UI.panel(trainer,[trainer],'account',1,k=>k),/Consent status not supplied/);
  assert.match(UI.panel(trainer,[trainer],'account',1,k=>k),/source_missing/);
});

test('workspace identity disambiguates identical routes and escapes attributes', () => {
  const a=view('trainer','id-a'),b=view('trainer','id-b');
  assert.notEqual(UI.workspaceLabel(a,0,k=>k),UI.workspaceLabel(b,0,k=>k));
  assert.match(UI.directory([a,b],a,0,k=>k,true),/data-workspace="id-b"/);
  const hostile=view('trainer','x" onclick="alert(1)');
  assert.doesNotMatch(UI.directory([hostile],null,0,k=>k),/data-workspace="x" onclick/);
});

test('review stages describe existing separate member trainer and apply boundaries', () => {
  const v=view('trainer');assert.equal(UI.reviewStatus(v),'noProposal');
  v.state.review={member:false,trainer:false};assert.equal(UI.reviewStatus(v),'memberReview');
  v.state.review.member=true;assert.equal(UI.reviewStatus(v),'trainerReview');
  v.state.review.trainer=true;assert.equal(UI.reviewStatus(v),'separateApply');
  v.state.route='B';v.state.review.trainer=false;assert.equal(UI.reviewStatus(v),'separateApply');
});

test('empty workspaces and historical navigation expose no write controls', () => {
  assert.deepEqual(UI.tabs(null),['account']);
  for(let language=0;language<3;language++) {
    assert.ok(UI.directory([],null,language,k=>k,true).includes(UI.words.noClients[language]));
    assert.doesNotMatch(UI.panel(null,[],'account',language,k=>k),/<button|<form/);
  }
  const historical={...view(),capabilities:{registration12:true}};
  assert.deepEqual(UI.tabs(historical),['training','account']);
  assert.match(UI.directory([historical],historical,1,k=>k),/data-destination="training"/);
});

test('notification status stays read-only and exact preference contract is preserved', () => {
  const v={...view(),notices:[{status:'pending'},{status:'seen'},{status:'expired'}]};
  assert.match(UI.notifications(v,1,k=>k),/Pending notifications: 1/);
  assert.doesNotMatch(UI.notifications(v,1,k=>k),/<input|data-action|<form/);
  assert.throws(()=>preferences({language:'nl',theme:'light',units:'metric',notifications:true}));
  assert.deepEqual(preferences({language:'nl',theme:'light',units:'metric'}),{language:'nl',theme:'light',units:'metric'});
});
