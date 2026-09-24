import copy,json,os,pathlib,subprocess,sys,time,unittest
from common import *
from local_cluster import Cluster
PSQL='C:/Program Files/PostgreSQL/18/bin/psql.exe'
class AuditTests(unittest.TestCase):
 @classmethod
 def sql(cls,q,ok=True):
    p=subprocess.run([PSQL,'-h','127.0.0.1','-p',str(cls.cluster.port),'-U','postgres','-d','postgres','-At','-v','ON_ERROR_STOP=1'],
      input=q,capture_output=True,encoding='utf8',timeout=30,creationflags=0x08000000 if os.name=='nt' else 0)
    if ok and p.returncode:raise AssertionError(p.stderr.splitlines()[0][:180])
    return p
 @classmethod
 def data(cls,q):
    p=cls.sql('select row_to_json(x) from ('+q+') x;')
    return json.loads([s for s in p.stdout.splitlines() if s.startswith(('{','['))][-1])
 @classmethod
 def setUpClass(cls):
    cls.cluster=Cluster()
    db=cls.cluster.start()
    try:assert db.query("select current_setting('server_version_num')")[0][0]=='170006'
    finally:db.close()
    try:
        cls.sql('create role anon;create role authenticated;create role service_role;')
        cls.sql((HERE/'audit.sql').read_text())
    except BaseException:cls.cluster.stop();raise
 @classmethod
 def tearDownClass(cls):cls.cluster.stop()
 def context(self,**kwargs):
    c=fresh();self.sql(register(c,**kwargs));return c
 def deny(self,c,body,reason):
    p=self.sql('do $q$begin '+start(c)+body+' end $q$;',False)
    self.assertNotEqual(p.returncode,0);self.assertIn(reason,p.stderr)
    ob=self.data(observations(c))
    self.assertEqual(ob['writes'],[])
    self.assertEqual(ob['action']['state'],'before_saved')
    return ob
 def test_exact_iud_commits_three_events_when_final_row_absent(self):
    c=fresh();b=self.data(snapshot(c));self.sql(register(c,before=digest(b)))
    self.sql('do $q$begin '+start(c)+insert(c)+f"update {A}.fixture set n=1 where id={lit(c['row'])};delete from {A}.fixture where id={lit(c['row'])};"+confirm(c)+' end $q$;')
    a=self.data(snapshot(c));o=self.data(observations(c));r=compare(c,b,a,o)
    self.assertEqual(r['writes'],3);self.assertIsNotNone(o['writes'][2]['old_key_sha'])
    self.sql(f"select {A}.seal_pair({lit(c['action'])},{lit(digest(a))},{lit(digest(r))});")
    self.assertFalse(self.data(observations(c))['enabled'])
 def test_default_disabled(self):
    c=self.context(enabled=False);self.deny(c,'','audit_not_admitted')
 def test_expired(self):
    c=self.context();self.sql(f"update {A}.runs set expires_at=clock_timestamp()-interval '1 second' where id={lit(c['run'])}")
    self.deny(c,'','audit_not_admitted')
 def test_extra_write_rolls_back(self):
    c=self.context(ops=('INSERT',));self.deny(c,insert(c)+f"update {A}.fixture set n=1 where id={lit(c['row'])};",'audit_unexpected_write')
 def test_wrong_row(self):
    c=self.context();self.deny(c,insert(c,row=str(uuid.uuid4())),'audit_unexpected_write')
 def test_forbidden_table(self):
    c=self.context();self.deny(c,insert(c,table='forbidden_fixture'),'audit_unexpected_write')
 def test_actor_mismatch(self):
    c=self.context();self.deny(c,insert(c,actor=str(uuid.uuid4())),'audit_actor_mismatch')
 def test_workspace_mismatch(self):
    c=self.context();self.deny(c,insert(c,workspace=str(uuid.uuid4())),'audit_workspace_mismatch')
 def test_ownership_move(self):
    c=self.context();self.deny(c,insert(c)+f"update {A}.fixture set actor_id={lit(str(uuid.uuid4()))} where id={lit(c['row'])};",'audit_actor_mismatch')
 def test_missing_operation(self):
    c=self.context();self.deny(c,insert(c)+confirm(c),'audit_missing_write')
 def test_duplicate_action(self):
    c=self.context(ops=());self.sql('do $q$begin '+start(c)+confirm(c)+' end $q$;')
    p=self.sql(f"select {A}.start_action({lit(c['action'])});",False)
    self.assertIn('audit_not_admitted',p.stderr)
 def test_cross_transaction_cannot_confirm(self):
    c=self.context(ops=());self.sql(f"select {A}.start_action({lit(c['action'])});")
    p=self.sql(f"select {A}.confirm_action({lit(c['action'])});",False)
    self.assertIn('audit_transaction_binding',p.stderr)
 def test_forged_guc_not_binding(self):
    c=self.context(ops=())
    p=self.sql("begin;select set_config('fmz6e11.audit_action',"+lit(c['action'])+",true);"+
      f"select {A}.confirm_action({lit(c['action'])});commit;",False)
    self.assertIn('audit_transaction_binding',p.stderr)
 def test_untrusted_roles_have_no_controls(self):
    for role in ('anon','authenticated','service_role'):
     p=self.sql('begin;set local role '+role+f";select * from {A}.runs;rollback;",False)
     self.assertNotEqual(p.returncode,0)
 def test_cleanup_seal_before_confirmation_fails(self):
    c=self.context()
    p=self.sql(f"select {A}.seal_pair({lit(c['action'])},repeat('a',64),repeat('b',64));",False)
    self.assertIn('audit_pair_order',p.stderr)
 def test_null_seal_not_accepted(self):
    c=self.context()
    p=self.sql(f"select {A}.seal_pair({lit(c['action'])},null,null);",False)
    self.assertIn('audit_pair_metadata',p.stderr)
 def test_trigger_disabled_fails_before_mutation(self):
    c=self.context()
    try:
     self.sql(f"alter table {A}.fixture disable trigger fmz6e11_tx_observer;")
     self.deny(c,'','audit_trigger_coverage')
    finally:self.sql(f"alter table {A}.fixture enable trigger fmz6e11_tx_observer;")
 def test_trigger_removed_fails_before_mutation(self):
    c=self.context()
    try:
     self.sql(f"drop trigger fmz6e11_tx_observer on {A}.fixture;")
     self.deny(c,'','audit_trigger_coverage')
    finally:self.sql(f"create trigger fmz6e11_tx_observer after insert or update or delete on {A}.fixture for each row execute function {A}.observe();")
 def test_two_identical_updates_not_deduplicated(self):
    c=self.context(ops=('INSERT','UPDATE','UPDATE','DELETE'))
    self.sql('do $q$begin '+start(c)+insert(c)+
     f"update {A}.fixture set n=0 where id={lit(c['row'])};update {A}.fixture set n=0 where id={lit(c['row'])};delete from {A}.fixture where id={lit(c['row'])};"+confirm(c)+' end $q$;')
    self.assertEqual(len(self.data(observations(c))['writes']),4)
 def test_changed_primary_key_is_bound_old_and_new(self):
    c=fresh();r=str(uuid.uuid4())
    contract=(f"jsonb_build_array(jsonb_build_object('table',{lit(A+'.fixture')},'op','INSERT','old',null,'new',{pk(c)}),"+
     f"jsonb_build_object('table',{lit(A+'.fixture')},'op','UPDATE','old',{pk(c)},'new',{pk(c,row=r)}),"+
     f"jsonb_build_object('table',{lit(A+'.fixture')},'op','DELETE','old',{pk(c,row=r)},'new',null))")
    self.sql(register(c,contract=contract));self.sql('do $q$begin '+start(c)+insert(c)+
     f"update {A}.fixture set id={lit(r)} where id={lit(c['row'])};delete from {A}.fixture where id={lit(r)};"+confirm(c)+' end $q$;')
    writes=self.data(observations(c))['writes'];self.assertNotEqual(writes[1]['old_key_sha'],writes[1]['new_key_sha'])

 def test_composite_key_and_pk_order(self):
    self.sql(f"create table {A}.composite_fixture(id uuid,slot int,actor_id uuid,workspace_id uuid,primary key(id,slot));")
    self.sql(f"select {A}.attach('{A}.composite_fixture','actor_id','workspace_id');")
    c=fresh();t=A+'.composite_fixture'
    k=f"{A}.pk_hash({lit(c['run'])},{lit(t)},jsonb_build_array({lit(c['row'])}::uuid,1))"
    e=(f"jsonb_build_array(jsonb_build_object('table',{lit(t)},'op','INSERT','old',null,'new',{k}),"+
      f"jsonb_build_object('table',{lit(t)},'op','DELETE','old',{k},'new',null))")
    self.sql(register(c,contract=e));self.sql('do $q$begin '+start(c)+
      f"insert into {t} values({lit(c['row'])},1,{lit(c['actor'])},{lit(c['workspace'])});delete from {t} where id={lit(c['row'])};"+confirm(c)+' end $q$;')
    w=self.data(observations(c))['writes'];self.assertEqual(w[0]['new_key_sha'],w[1]['old_key_sha'])
 def test_no_row_payload_columns(self):
    cols=self.sql(f"select column_name from information_schema.columns where table_schema='{A}' and table_name='writes';").stdout
    for word in ('email','password','token','payload','content','message'):self.assertNotIn(word,cols)
if __name__=='__main__':unittest.main()
