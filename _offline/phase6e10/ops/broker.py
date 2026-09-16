"""Fixed staging-only operator/test broker. IPC contains sessions; never log IPC."""
import hashlib
import json
import pathlib
import re
import secrets
import sys
import urllib.error
import uuid
import close6e9 as c

receipt = json.loads((c.ROOT / "supabase/.temp/phase6e9-owner-window.json").read_text())
names = {"memberA":"member", "trainerA":"trainer", "memberB":"b"}
expected = {"member":"zorgeyouri+6e9-a-lid@gmail.com","trainer":"zorgeyouri+6e9-a-trainer@gmail.com","b":"zorgeyouri+6e9-b-lid@gmail.com"}
accounts = {names[a["name"]]:a["id"] for a in receipt["accounts"]}
before_path = c.ROOT / "supabase/.temp/phase6e10-before.json"
controls_path = c.ROOT / "supabase/.temp/phase6e10-controls.json"
controls = json.loads(controls_path.read_text()) if controls_path.exists() else {}

def prove():
    rows = c.query("select p.id,p.email,p.role,p.trainer_id,u.email auth_email from public.profiles p join auth.users u on u.id=p.id where p.id in ("+",".join(c.lit(x) for x in accounts.values())+")")
    assert len(rows)==3
    for role, uid in accounts.items():
        row=next(x for x in rows if x["id"]==uid)
        assert row["email"]==row["auth_email"]==expected[role]
        assert row["role"]==("trainer" if role=="trainer" else "client")
        assert row["trainer_id"]==(accounts["trainer"] if role=="member" else None)

def service():
    if c.service is None:
        keys=c.call(c.MGMT+"/api-keys?reveal=true",method="GET")
        c.service=next(x["api_key"] for x in keys if x["name"]=="service_role")

def session(role):
    prove()
    if role in accounts:
        uid,email=accounts[role],expected[role]
    else:
        if role not in controls: raise RuntimeError("synthetic_control_missing")
        uid,email=controls[role]["id"],controls[role]["email"]
    service()
    current=c.call(c.BASE+"/auth/v1/admin/users/"+uid,method="GET",key=c.service)
    assert current["id"]==uid and current["email"]==email
    link=c.call(c.BASE+"/auth/v1/admin/generate_link",{"type":"magiclink","email":email},key=c.service)
    s=c.call(c.BASE+"/auth/v1/verify",{"type":"magiclink","token_hash":link["hashed_token"]},key=c.PUB)
    assert s["user"]["id"]==uid
    return s

def dispatch(d):
    op=d["op"]
    if op=="before":
        prove()
        if before_path.exists(): raise RuntimeError("before_snapshot_already_exists")
        fp=c.fingerprint(receipt)
        prior=json.loads((c.ROOT/"supabase/.temp/phase6e9-close-receipt.json").read_text())
        assert fp==prior["after"]
        migrations=c.query("select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sha256 from supabase_migrations.schema_migrations order by version")
        assert len(migrations)==34
        before_path.write_text(json.dumps({"tables":fp,"migrations":migrations},indent=2)+"\n")
        return {"tables":len(fp),"migrations":len(migrations),"equal_prior":True}
    if op=="after":
        prove()
        before=json.loads(before_path.read_text())
        fp=c.fingerprint(receipt)
        by_name=lambda rows: {r["name"]:r for r in rows}
        old,current=by_name(before["tables"]),by_name(fp)
        differences=[{"name":name,"before":old.get(name),"after":current.get(name)} for name in sorted(set(old)|set(current)) if old.get(name)!=current.get(name)]
        if differences:
            (c.ROOT/"supabase/.temp/phase6e10-data-differences.json").write_text(json.dumps(differences,indent=2)+"\n")
            raise RuntimeError("existing_data_fingerprint_difference")
        fp=sorted(fp,key=lambda r:r["name"])
        migrations=c.query("select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sha256 from supabase_migrations.schema_migrations order by version")
        if migrations[:34]!=before["migrations"] or len(migrations)!=38:
            raise RuntimeError("migration_history_difference")
        out={"tables":fp,"migrations":migrations,"all_existing_unchanged":True,"real_processing":False,"production_touched":False}
        (c.ROOT/"supabase/.temp/phase6e10-after.json").write_text(json.dumps(out,indent=2)+"\n")
        return {"unchanged_tables":len(fp),"migrations":len(migrations)}
    if op=="bootstrap":
        prove()
        if c.query("select id from fmz6e10_private.windows where status='active' and ends_at>clock_timestamp()"):
            raise RuntimeError("active_window_cannot_rotate_proof")
        existing=c.call(c.MGMT+"/secrets",method="GET")
        if any(x["name"]=="FMZ6E10_PROOF" for x in existing):
            raise RuntimeError("existing_proof_do_not_replace")
        rows=[]
        for role,uid in accounts.items():
            r={"member":"a_member","trainer":"a_trainer","b":"b_member"}[role]
            provenance=hashlib.sha256((uid+"|"+expected[role]+"|6e9-owner-accepted").encode()).hexdigest()
            rows.append("("+c.lit(uid)+","+c.lit(r)+","+c.lit(provenance)+")")
        proof=secrets.token_hex(32)
        c.call(c.MGMT+"/secrets",[{"name":"FMZ6E10_PROOF","value":proof}])
        c.query("begin;insert into fmz6e10_private.identities(user_id,role,provenance_sha) values"+",".join(rows)+";insert into fmz6e10_private.operators values("+c.lit(accounts["trainer"])+",true);update fmz6e10_private.config set enabled=true,proof_hash="+c.lit(hashlib.sha256(proof.encode()).hexdigest())+" where id;commit;")
        proof=None
        return {"identities":3,"operator":"synthetic_a_trainer_only","mail":0}
    if op=="identities":
        prove()
        return {**accounts,**{k:v["id"] for k,v in controls.items()}}
    if op=="session":
        return session(d["role"])
    if op=="controls":
        service()
        if controls: raise RuntimeError("inspect_existing_controls")
        for role in ["plain","foreign"]:
            email="6e10-"+role+"-"+uuid.uuid4().hex[:12]+"@example.invalid"
            u=c.call(c.BASE+"/auth/v1/admin/users",{"email":email,"password":secrets.token_urlsafe(32),"email_confirm":True},key=c.service)
            controls[role]={"id":u["id"],"email":email}
            controls_path.write_text(json.dumps(controls)+"\n")
            c.query("insert into public.profiles(id,email,role,name) values("+c.lit(u["id"])+","+c.lit(email)+","+c.lit("trainer" if role=="foreign" else "client")+",'6E10 synthetic denial control') on conflict(id) do update set role=excluded.role,email=excluded.email,name=excluded.name")
        return {"unenrolled_synthetic_controls":2,"mail":0}
    if op=="cleanup_controls":
        service()
        for role, a in list(controls.items()):
            u=c.call(c.BASE+"/auth/v1/admin/users/"+a["id"],method="GET",key=c.service)
            assert u["email"]==a["email"] and re.fullmatch(r"6e10-(plain|foreign)-[a-f0-9]{12}@example\.invalid",a["email"])
            c.query("begin;delete from auth.sessions where user_id="+c.lit(a["id"])+";delete from public.profiles where id="+c.lit(a["id"])+" and email="+c.lit(a["email"])+";commit;")
            c.call(c.BASE+"/auth/v1/admin/users/"+a["id"],{"should_soft_delete":False},method="DELETE",key=c.service)
            del controls[role]
            controls_path.write_text(json.dumps(controls)+"\n")
        return {"remaining_controls":0}
    if op=="query":
        sql=d["sql"]
        if len(sql)>100000 or not any(x in sql for x in ["fmz6e10_private","public.profiles","pg_proc","pg_class","pg_policies"]):
            raise RuntimeError("synthetic_query_scope_required")
        if "update public.profiles" in sql:
            if not any(c.lit(uid) in sql for uid in accounts.values()) or re.search(r"set\s+(?!trainer_id)",sql):
                raise RuntimeError("profile_write_scope_denied")
        return c.query(sql)
    raise RuntimeError("unknown_operation")

for line in sys.stdin:
    try:
        print(json.dumps({"ok":True,"result":dispatch(json.loads(line))}),flush=True)
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors="replace")
        code=re.search(r"synthetic_[a-z0-9_]+",body)
        print(json.dumps({"ok":False,"error":code.group(0) if code else "staging_api_rejected","status":e.code}),flush=True)
    except Exception as e:
        print(json.dumps({"ok":False,"error":str(e) if isinstance(e,RuntimeError) else "synthetic_precondition_failed"}),flush=True)
