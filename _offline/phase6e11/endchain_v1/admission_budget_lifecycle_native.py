"""Static source-owned lifecycle SQL expansion, without importing runtime code.

Only a small string-expression language is interpreted. No exec/eval, Python
artifact imports, query handles, fixture responses, subprocesses or sockets.
Dispatcher AST pins are independently enforced by admission_budget_release_joins.
"""
import ast
import hashlib
import pathlib

PREFIX = "_offline/phase6e11/endchain_v1/"
IO_SHA = "f3f78e4540931cd1a067f7baba69ef4dc8985a419d285768f7961e4bd27c0de3"
CLI_READER_SHA = "2c591cf72f6a5bca86baea81300b541e1e43821796312be3d5b3f8f9ff07ad4a"


def require(value, code):
    if not value:
        raise ValueError("lifecycle_native_" + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Strings:
    """Closed expression evaluator for the existing SQL constant builders."""
    def __init__(self):
        self.steps = 0
        self.functions = {}

    def expression(self, node, env):
        self.steps += 1
        require(self.steps <= 100_000, "expression_limit")
        if isinstance(node, ast.Constant) and type(node.value) in (str, bool, int, type(None)):
            return node.value
        if isinstance(node, ast.Name):
            require(node.id in env, "name:" + node.id)
            return env[node.id]
        if isinstance(node, (ast.Tuple, ast.List)):
            values = [self.expression(n, env) for n in node.elts]
            return tuple(values) if isinstance(node, ast.Tuple) else values
        if isinstance(node, ast.Dict):
            require(all(k is not None for k in node.keys), "dict_unpack")
            return {self.expression(k, env): self.expression(v, env) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.Attribute):
            value = self.expression(node.value, env)
            require(type(value) is dict and node.attr in value, "constant_attribute")
            return value[node.attr]
        if isinstance(node, ast.Subscript):
            value, key = self.expression(node.value, env), self.expression(node.slice, env)
            require(type(value) in (dict, tuple, list), "subscript_type")
            return value[key]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            a, b = self.expression(node.left, env), self.expression(node.right, env)
            require(type(a) is type(b) and type(a) in (str, list, tuple, int), "add_type")
            value = a + b
            require(type(value) is int or len(value) <= 1_000_000, "value_size")
            return value
        if isinstance(node, ast.IfExp):
            condition = self.expression(node.test, env)
            require(type(condition) is bool, "condition_type")
            return self.expression(node.body if condition else node.orelse, env)
        if isinstance(node, (ast.GeneratorExp, ast.ListComp)):
            require(len(node.generators) == 1, "generator_count")
            generator = node.generators[0]
            require(not generator.ifs and not generator.is_async, "generator_shape")
            values = self.expression(generator.iter, env)
            require(type(values) in (tuple, list) and len(values) <= 256, "generator_bound")
            result = []
            for value in values:
                local = dict(env)
                self.assign(generator.target, value, local)
                result.append(self.expression(node.elt, local))
            return result
        if isinstance(node, ast.Call):
            require(not node.keywords, "keyword_call")
            args = [self.expression(n, env) for n in node.args]
            if isinstance(node.func, ast.Attribute):
                owner = self.expression(node.func.value, env)
                method = node.func.attr
                if type(owner) is str and method == "replace" and len(args) == 2 and all(type(v) is str for v in args):
                    return owner.replace(*args)
                if type(owner) is str and method == "join" and len(args) == 1 and type(args[0]) in (list, tuple):
                    require(all(type(v) is str for v in args[0]), "join_type")
                    return owner.join(args[0])
                if type(owner) is dict and method == "items" and not args:
                    return list(owner.items())
            if isinstance(node.func, ast.Name) and node.func.id in self.functions:
                function = self.functions[node.func.id]
                require(len(args) == len(function.args.args), "function_arity")
                local = dict(env, **dict(zip((n.arg for n in function.args.args), args)))
                for statement in function.body:
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                        self.assign(statement.targets[0], self.expression(statement.value, local), local)
                    elif isinstance(statement, ast.Return):
                        return self.expression(statement.value, local)
                    else:
                        raise ValueError("lifecycle_native_builder_statement")
            raise ValueError("lifecycle_native_call_denied")
        raise ValueError("lifecycle_native_expression_denied:" + type(node).__name__)

    def assign(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = value
            return
        require(isinstance(target, (ast.Tuple, ast.List)) and type(value) in (tuple, list)
                and len(target.elts) == len(value), "assignment_shape")
        for node, part in zip(target.elts, value):
            self.assign(node, part, env)

    def constants(self, tree, names, initial=None):
        env = dict(initial or {})
        found = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name in names:
                    env[name] = self.expression(node.value, env)
                    found.add(name)
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id in names:
                require(isinstance(node.op, ast.Add), "augmented_operation")
                env[node.target.id] += self.expression(node.value, env)
        require(found == set(names), "constants_missing:" + repr(sorted(set(names) - found)))
        return {name: env[name] for name in names}


def lifecycle_program(root, runtime_dir):
    root, runtime = pathlib.Path(root), pathlib.Path(runtime_dir)
    hashes, originals = {}, {}
    def read(name):
        path = runtime / name.split("/", 1)[1] if name.startswith("quota_candidate_v1/") else root / PREFIX / name
        raw = path.read_bytes()
        require(len(raw) <= 2_000_000, "source_size")
        hashes[PREFIX + name], originals[path] = sha(raw), raw
        return ast.parse(raw)
    strings = Strings()
    legacy = strings.constants(read("migration_boundary.py"), ("VERSION", "TARGET", "CONSTRAINTS"))
    quota_boundary = strings.constants(read("quota_boundary.py"), ("VERSION", "TARGET", "CONSTRAINTS"), dict(legacy=legacy))
    gates = strings.constants(read("lifecycle_gates.py"), ("CATALOG", "MIGRATIONS", "ACCESS", "ABSENCE", "FINAL"), quota_boundary)
    quota = strings.constants(read("admission_quota_readonly.py"), ("QUERIES",))
    compiler = strings.constants(read("quota_candidate_v1/compiler.py"), ("SCHEMA", "FUNCTION", "PREFIX"))
    catalog_tree = read("quota_candidate_v1/runtime_catalog.py")
    strings.functions = {n.name: n for n in catalog_tree.body if isinstance(n, ast.FunctionDef)
                         and n.name in ("array_query", "catalog_sql")}
    require(set(strings.functions) == {"array_query", "catalog_sql"}, "catalog_builders_missing")
    names = [n.targets[0].id for n in catalog_tree.body if isinstance(n, ast.Assign)
             and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
             and (n.targets[0].id.endswith("_QUERY") or n.targets[0].id in
                  ("SCHEMA", "FUNCTION", "CATALOG_BEFORE", "CATALOG_AFTER"))]
    catalog = strings.constants(catalog_tree, names, dict(compiler=compiler, quota=quota, gates=gates))
    history = strings.constants(read("quota_candidate_v1/runtime_history.py"), ("MIGRATIONS",))
    life = strings.constants(read("quota_candidate_v1/runtime_lifecycle.py"), ("_FRAGMENT", "FINAL"),
                             dict(gates=gates, runtime_catalog=catalog))
    io = strings.constants(read("integral_io.py"), ("SNAPSHOT",))
    require(hashes[PREFIX + "integral_io.py"] == IO_SHA, "query_io_dispatch_source_changed")
    # The caller verifies exact _gate/_final/_monitor/_readonly ASTs. QueryIO is
    # fully pinned above, including its cold bind cache and two-command close.
    bind = "EXPLAIN (VERBOSE,COSTS FALSE,FORMAT JSON) "
    closing = "EXPLAIN (ANALYZE,BUFFERS,WAL,VERBOSE,COSTS FALSE,FORMAT JSON) "
    snapshot = io["SNAPSHOT"]
    profiles = {}
    def commands(rows, prefix):
        from sql_protocol import statements
        result = []
        for index, (phase, text, args) in enumerate(rows):
            parsed = statements(text)
            require(len(parsed) == 1, "single_protocol_command")
            result.append(dict(index=index, phase=prefix + phase,
                sql_sha256=sha(text.encode()), statement_sha256=parsed[0]["sha256"],
                sql_kind=parsed[0]["kind"], protocol_commands=1, argument_source=args,
                read_wal_proven=False, runtime_values_observed=False))
        return result
    for label in ("before", "after_migration", "final_pre", "final_post"):
        rows = [("begin", "BEGIN TRANSACTION READ ONLY", "none")]
        if label != "final_post":
            rows += [("timeout", "SET LOCAL statement_timeout='5s'", "none"),
                     ("readonly", "select current_setting('transaction_read_only')='on' readonly", "none")]
        rows += [("io_bind", bind + snapshot, "query_id_list"), ("io_sample", snapshot, "query_id_list")]
        checks = [("metadata", life["FINAL"], "final_parameters(ids,fixture_context,stage)")]
        if label in ("before", "after_migration"):
            checks = [("access", gates["ACCESS"], "ids.values"),
                      ("migrations", history["MIGRATIONS"], "history.inspect_versions"),
                      ("catalog", catalog["CATALOG_AFTER" if label == "after_migration" else "CATALOG_BEFORE"], "temporary_schemas"),
                      ("absence", gates["ABSENCE"], "temporary_schemas,ids.values,window")]
        require(len({text for _, text, _ in checks}) == len(checks) and snapshot not in {text for _, text, _ in checks},
                "query_io_cold_cache_shape")
        for name, text, args in checks:
            rows += [("io_bind", bind + text, args), ("io_sample", snapshot, "query_id_list"), (name, text, args)]
        rows += [("io_sample", snapshot, "query_id_list"), ("io_closing_witness", closing + snapshot, "query_id_list"),
                 ("rollback", "ROLLBACK", "none")]
        profiles[label] = commands(rows, "gates_" + label + "_")
    guard = strings.constants(read("integral_stream.py"), ("GUARD",))["GUARD"]
    reader = strings.constants(read("cli_stat_reader.py"), ("SQL",))["SQL"]
    require(hashes[PREFIX + "cli_stat_reader.py"] == CLI_READER_SHA, "cli_reader_source_changed")
    ancillary = dict(preflight=commands([
        ("begin", "BEGIN TRANSACTION READ ONLY", "none"), ("identity", guard, "none"),
        ("history", history["MIGRATIONS"], "history.inspect_versions"), ("rollback", "ROLLBACK", "none")], "preflight_"),
        cli_observer=commands([("begin", "BEGIN TRANSACTION READ ONLY", "none"),
            ("readonly", "select current_setting('transaction_read_only')='on' readonly", "none"),
            ("statistics", reader, "none"), ("rollback", "ROLLBACK", "none")], "cli_observer_"))
    for path, raw in originals.items():
        require(path.read_bytes() == raw, "source_changed_during_compile")
    hashes[PREFIX + pathlib.Path(__file__).name] = sha(pathlib.Path(__file__).read_bytes())
    return dict(format="actual-lifecycle-native-source-v1", profiles=profiles, ancillary_profiles=ancillary, source_hashes=hashes,
                explicit_sql=sum(map(len, profiles.values())), sql_executed=0,
                statement_template_identity_proven=True, actual_execution_evidence=False,
                read_wal_proven=False, hosted_admitted=False)
