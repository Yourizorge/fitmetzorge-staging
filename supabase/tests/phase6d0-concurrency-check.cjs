// Controlled STAGING concurrency fixtures. CLI credentials stay in its OS credential store.
const fs=require("fs"),os=require("os"),path=require("path"),crypto=require("crypto"),{execFile}=require("child_process");
const cli=process.env.SUPABASE_CLI;
if(!cli)throw new Error("SUPABASE_CLI required");
const project="mokxyyullfhkfalopbzd";
const member=crypto.randomUUID(),trainer=crypto.randomUUID(),suffix=member.replaceAll("-","");
const email="6d0-race-"+suffix+"@example.invalid",trainerEmail="6d0-race-trainer-"+suffix+"@example.invalid";
const dir=fs.mkdtempSync(path.join(os.tmpdir(),"fmz-6d0-race-"));
const lit=x=>"'"+String(x).replaceAll("'","''")+"'";
async function query(sql){
 const file=path.join(dir,crypto.randomUUID()+".sql");fs.writeFileSync(file,sql);
 try{return await new Promise(resolve=>execFile(cli,["db","query","--linked","--project-ref",project,"--file",file,"--output","json"],{windowsHide:true,timeout:90000,maxBuffer:1048576},(err,out)=>{
  try{const parsed=JSON.parse(out);resolve({ok:!err&&!!parsed.rows,rows:parsed.rows||[],error:JSON.stringify(parsed.error||{})});}
  catch{resolve({ok:false,rows:[],error:"transport_failure"});}
 }));}finally{fs.rmSync(file,{force:true});}
}
const asMember=sql=>"begin; select set_config('request.jwt.claim.sub',"+lit(member)+",true); set local role authenticated; "+sql+"; commit;";
const checks=[];const check=(name,ok)=>{if(!ok)throw new Error(name);checks.push(name);};
(async()=>{
 try{
  check("fixtures_created",(await query("begin; insert into auth.users(id,aud,role,email,email_confirmed_at) values("+lit(member)+"::uuid,'authenticated','authenticated',"+lit(email)+",now()),("+lit(trainer)+"::uuid,'authenticated','authenticated',"+lit(trainerEmail)+",now()); insert into public.profiles(id,role,name,email) values("+lit(trainer)+"::uuid,'trainer','Synthetic race trainer',"+lit(trainerEmail)+"); insert into public.coach_workspaces(trainer_id,state) values("+lit(trainer)+"::uuid,jsonb_build_object('clients',jsonb_build_array(jsonb_build_object('id','race-slot','email',"+lit(email)+",'water',0)))); commit; select true as ready;")).ok);
  const issued=await query("begin; select set_config('request.jwt.claim.sub',"+lit(trainer)+",true); set local role authenticated; select public.fmz_phase6d0_issue_client_invite('race-slot') as invitation; commit;");
  check("fixture_invitation_issued",issued.ok&&issued.rows[0]?.invitation?.token);
  const token=issued.rows[0].invitation.token;
  const slowAccept=asMember("select pg_advisory_xact_lock(hashtextextended('fmz6d0:invite-email:'||"+lit(email)+",0)); select pg_sleep(2); select (public.fmz_phase6d0_accept_client_invite("+lit(token)+")).role as linked");
  const fastAccept=asMember("select (public.fmz_phase6d0_accept_client_invite("+lit(token)+")).role as linked");
  const accept=await Promise.all([query(slowAccept),query(fastAccept)]);
  check("concurrent_accept_exactly_one_success",accept.filter(x=>x.ok).length===1);
  check("concurrent_replay_rejected",accept.some(x=>!x.ok&&x.error.includes("invitation_used_expired_or_revoked")));
  const read=await query(asMember("select public.fmz_phase6d0_read_own_workspace() as workspace"));
  check("own_workspace_read",read.ok&&read.rows[0]?.workspace?.revision);
  const w=read.rows[0].workspace,rev=w.revision,item=w.state.clients[0];
  const saves=await Promise.all([1,2].map(n=>query(asMember("select public.fmz_phase6d0_save_own_workspace("+lit(JSON.stringify({...item,water:n}))+"::jsonb,"+lit(rev)+") as saved"))));
  check("concurrent_workspace_exactly_one_success",saves.filter(x=>x.ok).length===1);
  check("concurrent_workspace_stale_rejected",saves.some(x=>!x.ok&&x.error.includes("workspace_conflict_reload_required")));
 }finally{
  const cleanup=await query("begin; do $$ begin if exists(select 1 from auth.users where id in ("+lit(member)+"::uuid,"+lit(trainer)+"::uuid) and email not in ("+lit(email)+","+lit(trainerEmail)+")) then raise exception 'fixture_cleanup_identity_mismatch'; end if; end $$; delete from legacy_auth_private.client_invitations where trainer_id="+lit(trainer)+"::uuid; delete from public.coach_workspaces where trainer_id="+lit(trainer)+"::uuid; delete from public.profiles where id="+lit(member)+"::uuid; delete from public.profiles where id="+lit(trainer)+"::uuid; delete from auth.users where id in ("+lit(member)+"::uuid,"+lit(trainer)+"::uuid); commit; select count(*) as remaining from auth.users where id in ("+lit(member)+"::uuid,"+lit(trainer)+"::uuid);");
  check("all_concurrency_fixtures_removed",cleanup.ok&&Number(cleanup.rows[0]?.remaining)===0);
  if(path.dirname(path.resolve(dir))!==path.resolve(os.tmpdir())||!path.basename(dir).startsWith("fmz-6d0-race-"))throw new Error("unsafe_fixture_directory");
  fs.rmSync(dir,{recursive:true,force:true});
 }
 console.log(JSON.stringify({scope:"phase6d0_staging_concurrency",overall_pass:true,pass_count:checks.length,checks,external_calls:0}));
})().catch(e=>{console.error(JSON.stringify({scope:"phase6d0_staging_concurrency",overall_pass:false,failed:e.message,checks}));process.exitCode=1;});
