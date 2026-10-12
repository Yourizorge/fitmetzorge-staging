"""Bound the unchanged digest transport to the 155 existing M42 tables."""
import hashlib,math,os,time
import discovery as d
from guard import Stop,save,digest

t=d.t
TABLE_LIMIT=155

def check_plan(plan):
    names=[p['name'] for p in plan]
    if len(plan)!=TABLE_LIMIT or len(set(names))!=TABLE_LIMIT or any(len(p['cohorts'])!=1 or p['cohorts']!={'protected':'true'} for p in plan):
        raise Stop('controller_exact_155_table_plan')
    if not {'fmz6e11_request_private.control','fmz6e11_request_private.receipts'}.issubset(names):
        raise Stop('controller_m42_tables_missing')

class ControllerCursor(d.HostedCursor):
    def transfer(self,sql,plan,size,bindings,inject=None):
        check_plan(plan)
        self.plan=plan;declaration=t.declare_sql(sql)
        for name,command in [('declare',declaration),('fetch',t.fetch_sql(size)),('close',t.CLOSE)]:
            if bindings[name]['sql_sha256']!=hashlib.sha256(command.encode()).hexdigest():raise Stop('utility_source_binding')
        self.utility(declaration,bindings['declare']['queryid'],'cursor_declare')
        reducer=t.Reducer(plan,self.path/'chunks');frames=[];before=None
        for page in range(math.ceil(t.MAX_ROWS/size)+1):
            name=f'fetch_{page:03d}'
            rows,before,frame=self.utility(t.fetch_sql(size),bindings['fetch']['queryid'],name,before,size)
            if inject=='after_chunk':raise Stop('injected_after_chunk_before_reducer')
            frames.append(frame)
            if not rows:break
            for row in rows:reducer.add(row)
            if reducer.rows>t.MAX_ROWS:raise Stop('total_row_budget')
        else:raise Stop('missing_terminal_empty_fetch')
        self.utility(t.CLOSE,bindings['close']['queryid'],'cursor_close')
        if self.command(t.SNAPSHOT,'final_snapshot_identity')!=self.snapshot:raise Stop('snapshot_changed')
        final=t.old.s.identity(self.command(t.old.s.CHECK,'final_transaction_identity'))
        if not t.old.same_transaction(final,self.transaction):raise Stop('transaction_changed')
        save(self.path/'transaction-final.json',final)
        started=time.monotonic();tables=reducer.finish(reducer.rows)
        report={'tables':tables,'rows':reducer.rows,'frames':frames,'final_local_merge_seconds':time.monotonic()-started,
            'sort_chunk_rows':16384,'sort_files':len(reducer.chunks),'digest_disk_bytes':reducer.written,
            'bounded_disk_bytes':t.MAX_ROWS*(4+1+64+1+t.MAX_FLAGS+1),'algorithm':t.ALGORITHM,'canonical':t.CANONICAL,
            'table_limit':TABLE_LIMIT,'original_table_limit':t.MAX_TABLES,
            'adapter_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest()}
        save(self.path/'transfer-complete.json',report)
        return report
