"""Read-only source template inventory; never SQL execution or case admission.

Lexical order and structured branch scopes are exported separately. They are
not a fabricated runtime trace. Unresolved SQL and call arguments stay unknown.
"""
import ast
import json
import os
import pathlib
import re
import subprocess

from sql_protocol import parser, statements
from .compiler import canonical, read_source, require, sha

PREFIX = '_offline/phase6e11/endchain_v1/'
OWN_PREFIX = PREFIX + 'quota_candidate_v1/'
HERE = pathlib.Path(__file__).resolve().parent
FORMAT = 'quota-native-template-catalog-v1'
PYTHON_SOURCES = tuple(PREFIX + name for name in (
    'integral_io.py', 'integral_stream.py', 'integral_ci.py',
    'registered_runner.py', 'registered_lifecycle.py', 'control_recovery.py',
    'safety_auth.py', 'safety_auth_native.py', 'auth_evidence.py', 'auth_protocol.py',
    'lifecycle_gates.py', 'cli_stat_reader.py', 'sql_protocol.py')) + tuple(
    OWN_PREFIX + name for name in (
        'runtime_adapter.py', 'runtime_parent_workflow.py', 'runtime_recovery.py',
        'runtime_prefix.py', 'runtime_history.py', 'runtime_stream.py',
        'runtime_bootstrap_closeout.py', 'runtime_faults.py'))
PENDING_SOURCES = (OWN_PREFIX + 'runtime_catalog.py', OWN_PREFIX + 'runtime_lifecycle.py')
NODE_SOURCES = tuple('_offline/phase6e11/' + name for name in (
    'controller_v1/core.mjs', 'controller_v1/store.mjs',
    'endchain_v1/native_store.mjs', 'endchain_v1/session_transport.mjs',
    'endchain_v1/request_transport.mjs', 'endchain_v1/quota_candidate_v1/runtime_node.mjs',
    'endchain_v1/quota_candidate_v1/runtime_workflow.mjs',
    'endchain_v1/quota_candidate_v1/runtime_integral_workflow.mjs'))


def tree_sha(node):
    return sha(ast.dump(node, include_attributes=False).encode())


def callable_name(node):
    if isinstance(node, ast.Name):return node.id
    if isinstance(node, ast.Attribute):return callable_name(node.value) + '.' + node.attr
    if isinstance(node, ast.Subscript):return callable_name(node.value) + '[]'
    return '<dynamic>'


class SourceCatalog:
    def __init__(self, root, runtime_dir):
        parser()
        self.root=pathlib.Path(root).resolve(strict=True)
        self.runtime=pathlib.Path(runtime_dir).resolve(strict=True)
        self.modules={};self.sources={};self.sites=[];self.methods=[]

    def raw(self, name):
        require(name.startswith('_offline/') and '\\' not in name
            and '..' not in pathlib.PurePosixPath(name).parts, 'template_source_path')
        if name.startswith(OWN_PREFIX):
            relative=name[len(OWN_PREFIX):]
            require(pathlib.PurePosixPath(relative).name==relative, 'template_runtime_path')
            path=self.runtime/relative
            require(not path.is_symlink() and path.resolve().parent==self.runtime,
                'template_runtime_path')
            raw=path.read_bytes()
        else:raw=read_source(self.root,name)
        require(len(raw)<=2000000, 'template_source_size')
        self.sources[name]=sha(raw)
        return raw

    def module(self, name):
        if name in self.modules:return self.modules[name]
        require(len(self.modules)<128, 'template_import_bound')
        tree=ast.parse(self.raw(name))
        assignments={};imports={}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                assignments[node.targets[0].id]=node.value
            elif isinstance(node,ast.ImportFrom) and node.module and node.level==0:
                for alias in node.names:imports[alias.asname or alias.name]=(node.module,alias.name)
        signatures={}
        def functions(nodes, parent=''):
            for node in nodes:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    symbol=parent+'.'+node.name if parent else node.name
                    if not isinstance(node,ast.ClassDef):
                        signatures[symbol]=[x.arg for x in (*node.args.posonlyargs,*node.args.args)]
                    functions(node.body,symbol)
        functions(tree.body)
        result=dict(tree=tree,assignments=assignments,imports=imports,signatures=signatures)
        self.modules[name]=result
        return result

    def literal(self, node, name, local, seen=frozenset()):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,int,bool)):return node.value
        if isinstance(node,ast.Name):
            key=(name,node.id)
            if key in seen:return None
            module=self.module(name)
            value=local.get(node.id,module['assignments'].get(node.id))
            if value is not None:return self.literal(value,name,local,seen|{key})
            imported=module['imports'].get(node.id)
            if imported and re.fullmatch('[a-z][a-z0-9_]*',imported[0]):
                target=PREFIX+imported[0]+'.py'
                if target in PYTHON_SOURCES or target in PENDING_SOURCES:
                    return self.literal(ast.Name(id=imported[1]),target,{},seen|{key})
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
            a=self.literal(node.left,name,local,seen);b=self.literal(node.right,name,local,seen)
            if type(a) is type(b) and isinstance(a,(str,int)):return a+b
        return None

    def add_site(self, node, source, symbol, scope, local):
        callee=callable_name(node.func)
        leaf=callee.split('.')[-1]
        if leaf in ('before_sql','after_sql','charge','safety','confirm','confirm_safety'):
            return
        channel=phase=sql=None
        dispatch_class=None
        if leaf in ('query','raw_query'):
            signatures=self.module(source)['signatures']
            parent=symbol
            formal=None
            while parent:
                key=parent+'.'+callee
                if key in signatures:formal=signatures[key];break
                parent=parent.rpartition('.')[0]
            if formal is None:formal=signatures.get(callee)
            if formal and 'self' in formal[:1]:formal=formal[1:]
            if formal:
                arguments=dict(zip(formal,node.args))
                arguments.update({kw.arg:kw.value for kw in node.keywords if kw.arg})
                channel=arguments.get('channel');phase=arguments.get('phase')
                sql=next((arguments[k] for k in ('text','sql','q') if k in arguments),None)
            elif len(node.args)>=3 and (source==PREFIX+'integral_io.py' or
                    self.literal(node.args[0],source,local) in ('reader','writer','setup','workflow')):
                channel,phase,sql=node.args[:3]
            dispatch_class='query_callback' if sql is not None else 'dynamic_dispatch_arguments'
        elif leaf in ('execute','sql','outer','lock_query') and node.args:
            sql=node.args[0];dispatch_class='native_or_outer_dispatch'
        elif callee in ('monitor.bind','monitor.start','monitor.sample','monitor.checkpoint','monitor.close') or (
                source==PREFIX+'integral_io.py' and callee in
                ('self.bind','self.start','self.sample','self.checkpoint','self.close')):
            dispatch_class='query_io_call'
        elif leaf in ('raw_query','query','execute','sql','outer','lock_query'):
            dispatch_class='dynamic_dispatch_arguments'
        else:return
        resolve=lambda n:self.literal(n,source,local) if n is not None else None
        text=resolve(sql)
        known=type(text) is str
        parsed=None
        if known:
            from pglast.parser import ParseError
            try:
                parsed=[{k:v for k,v in row.items() if k!='sql'} for row in statements(text)]
            except ParseError:
                # A known source string is not necessarily a complete SQL query.
                parsed=None
        inputs=sorted({n.id for n in ast.walk(sql) if isinstance(n,ast.Name)}) if sql is not None else []
        row=dict(source=source,symbol=symbol,line=node.lineno,
            source_order=len(self.sites)+1,callee=callee,dispatch_class=dispatch_class,
            channel=resolve(channel),phase=resolve(phase),scope=list(scope),
            call_ast_sha256=tree_sha(node),sql_expression_sha256=tree_sha(sql) if sql is not None else None,
            sql_sha256=sha(text.encode()) if known else None,
            statements=parsed,protocol_commands=len(parsed) if parsed is not None else None,
            unresolved_inputs=inputs if not known else [],
            dynamic_sql=sql is not None and not known,
            transaction_boundary=parsed[0]['kind'] if parsed and len(parsed)==1
                and parsed[0]['kind']=='TransactionStmt' else None,
            execution_observed=False)
        self.sites.append(row)

    def walk_expr(self, node, source, symbol, scope, local):
        # Arguments are evaluated before their enclosing call. Export that order.
        for child in ast.iter_child_nodes(node):
            self.walk_expr(child,source,symbol,scope,local)
        if isinstance(node,ast.Call):self.add_site(node,source,symbol,scope,local)

    def block(self, nodes, source, symbol, scope, local):
        local=dict(local)
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                nested=symbol+'.'+node.name if symbol else node.name
                self.methods.append(dict(source=source,symbol=nested,line=node.lineno,
                    ast_sha256=tree_sha(node),execution_observed=False))
                parameters={} if isinstance(node,ast.ClassDef) else {
                    arg.arg:ast.Name(id=arg.arg) for arg in
                    (*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs)}
                self.block(node.body,source,nested,(),parameters)
                continue
            if isinstance(node,ast.If):
                self.walk_expr(node.test,source,symbol,scope,local)
                condition=dict(kind='if',line=node.lineno,condition_sha256=tree_sha(node.test))
                self.block(node.body,source,symbol,(*scope,{**condition,'branch':'true'}),local)
                self.block(node.orelse,source,symbol,(*scope,{**condition,'branch':'false'}),local)
                # Branch writes cannot be represented by a single unconditional value.
                writes={n.id for branch in (node.body,node.orelse) for statement in branch
                    for n in ast.walk(statement) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
                for key in writes:local[key]=ast.Name(id=key)
                if any(isinstance(n,(ast.Return,ast.Raise)) for n in node.body):
                    scope=(*scope,{**condition,'branch':'false_after_terminal_true_branch'})
                continue
            if isinstance(node,(ast.For,ast.While,ast.Try,ast.With)):
                kind=type(node).__name__.lower()
                control=dict(kind=kind,line=node.lineno,condition_sha256=tree_sha(node))
                if isinstance(node,ast.For):self.walk_expr(node.iter,source,symbol,scope,local)
                if isinstance(node,ast.While):self.walk_expr(node.test,source,symbol,scope,local)
                if isinstance(node,ast.With):
                    for item in node.items:self.walk_expr(item.context_expr,source,symbol,scope,local)
                self.block(node.body,source,symbol,(*scope,{**control,'branch':'body'}),local)
                if isinstance(node,ast.Try):
                    for i,handler in enumerate(node.handlers):
                        self.block(handler.body,source,symbol,(*scope,{**control,'branch':'except_'+str(i)}),local)
                    self.block(node.finalbody,source,symbol,(*scope,{**control,'branch':'finally'}),local)
                if hasattr(node,'orelse'):
                    self.block(node.orelse,source,symbol,(*scope,{**control,'branch':'else'}),local)
                continue
            self.walk_expr(node,source,symbol,scope,local)
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name):local[target.id]=node.value
            if isinstance(node,(ast.Return,ast.Raise)):break


def reconcile_historical(rows, sites):
    """Exact template hash matches are references, not ordered execution proof."""
    known={}
    for site in sites:
        for statement in site.get('statements') or []:
            known.setdefault(statement['sha256'],[]).append(dict(source=site['source'],
                symbol=site['symbol'],line=site['line'],source_order=site['source_order']))
    result=[]
    for row in rows:
        if row.get('kind') not in ('native','observer'):continue
        digest=row.get('sql_sha256')
        matches=known.get(digest,[])
        result.append(dict(id=row['id'],action=row['action'],sql_sha256=digest,
            matching_source_sites=matches,
            classification='exact_template_hash_only' if matches else 'unresolved_template_or_binding',
            ordered_execution_equivalence_proven=False,execution_observed=False))
    return result


def export_node_factories(catalog):
    """Run genuine source builders with inert SQL handles, not a database driver."""
    refs=json.loads(catalog.raw(OWN_PREFIX+'runtime_refs.json'))
    names=set(NODE_SOURCES) | {name for name in refs['references'] if name.endswith('.mjs')}
    sources={name:dict(source=catalog.raw(name).decode('utf-8'),sha256=catalog.sources[name])
        for name in sorted(names)}
    script=catalog.runtime/'runtime_native_templates.mjs'
    expected=sha(catalog.raw(OWN_PREFIX+'runtime_native_templates.mjs'))
    require(sha(script.read_bytes())==expected,'template_node_source')
    payload=dict(format='quota-native-source-probe-v1',sources=sources)
    result=subprocess.run(['node','--experimental-vm-modules',str(script)],
        input=canonical(payload),capture_output=True,timeout=5,
        env={k:v for k,v in os.environ.items() if k in ('PATH','Path','SYSTEMROOT','SystemRoot')})
    require(result.returncode==0 and len(result.stdout)<=1000000,'template_node_probe_failed')
    value=json.loads(result.stdout)
    require(value.get('format')==payload['format'] and value.get('sql_executed')==0
        and value.get('network_calls')==0 and value.get('full_chain_admission') is False,
        'template_node_probe_scope')
    require(value['source_hashes'] and all(sources.get(name,{}).get('sha256')==digest
        for name,digest in value['source_hashes'].items()),'template_node_probe_binding')
    sites=[]
    for probe in value['profiles']:
        require(probe['source'] in value['source_hashes'] and probe['execution_observed'] is False,
            'template_node_probe_origin')
        for index,row in enumerate(probe['sites']):
            parsed=statements(row['sql'])
            sites.append(dict(source=probe['source'],symbol=probe['symbol'],line=None,
                source_order=index+1,profile=probe['name'],conditions=probe['conditions'],
                callee='actual_source_factory_with_inert_sql',dispatch_class='source_factory_probe',
                phase=row['phase'],channel=row['channel'],sql_sha256=sha(row['sql'].encode()),
                statements=[{k:v for k,v in p.items() if k!='sql'} for p in parsed],
                protocol_commands=len(parsed),arguments_count=row['args_count'],dynamic_sql=False,
                unresolved_inputs=['runtime_bound_values_not_supplied_or_observed'],
                transaction_boundary=parsed[0]['kind'] if len(parsed)==1
                    and parsed[0]['kind']=='TransactionStmt' else None,
                execution_observed=False))
    return dict(source_hashes=value['source_hashes'],sites=sites,profile_count=len(value['profiles']),
        condition_coverage='store_templates_and_session_success_cold_warm_only',
        admission_not_exercised=True,sql_executed=0,full_chain_admission=False)


def export_native_templates(root, *, runtime_dir=HERE, historical_rows=(), node_factories=False):
    parser()
    catalog=SourceCatalog(root,runtime_dir)
    missing=[]
    for source in (*PYTHON_SOURCES,*PENDING_SOURCES):
        try:module=catalog.module(source)
        except (OSError,ValueError):
            if source not in PENDING_SOURCES:raise
            missing.append(dict(source=source,reason='required_lifecycle_source_not_delivered'))
            continue
        catalog.block(module['tree'].body,source,'',(),{})
    # Node execution templates require a source-bound exporter of their own;
    # never parse arbitrary JavaScript with regex and call its branches covered.
    for source in NODE_SOURCES:
        catalog.raw(source)
        missing.append(dict(source=source,reason='node_dispatch_template_and_branch_join_required'))
    node=export_node_factories(catalog) if node_factories else None
    if node is not None:catalog.sites.extend(node['sites'])
    catalog.raw(OWN_PREFIX+'runtime_native_templates.py')
    matches=reconcile_historical(historical_rows,catalog.sites)
    return dict(format=FORMAT,sources=catalog.sources,methods=catalog.methods,sites=catalog.sites,
        historical_reconciliation=matches,missing_sources_or_dispatchers=missing,node_factories=node,
        unresolved_dispatches=[dict(source=s['source'],symbol=s['symbol'],line=s['line'],
            unresolved_inputs=s['unresolved_inputs']) for s in catalog.sites
            if s['dynamic_sql'] or s['dispatch_class']=='dynamic_dispatch_arguments'],
        source_order_is_not_runtime_order=True,native_template_reconciliation_complete=False,
        sql_executed=0,full_chain_admission=False,hosted_admission=False)
