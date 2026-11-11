"""Pure accounting replay of original root members against a trusted compiler.

The caller must independently compile trusted_root from reviewed source, never
take it from the archive. This proves accounting consistency, not SQL execution,
case semantics, artifact authenticity, runtime admission or hosted permission.
No candidate imports, ledger reconstruction, filesystem or external operations.
"""
import copy
import hashlib
import json
import re
import uuid

import admission_budget_root_runtime as root


def need(condition, code):
    root.require(condition, "root_replay_" + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(items):
    value = {}
    for key, item in items:
        need(key not in value, "duplicate_json_key")
        value[key] = item
    return value


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
            parse_constant=lambda _: need(False, "nonfinite_json"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise root.RootBlocked("root_replay_invalid_json") from error


def _number(value):
    return type(value) is int and value >= 0


def _hash(value):
    return type(value) is str and re.fullmatch("[a-f0-9]{64}", value) is not None


def _originals(originals, refs):
    need(type(originals) is dict and type(refs) is dict
        and set(refs) == {"evidence_refs", "journal_refs"}, "input_shape")
    evidence, journals = refs["evidence_refs"], refs["journal_refs"]
    need(type(evidence) is list and 2 <= len(evidence) <= 16
         and type(journals) is list and 1 <= len(journals) <= 32, "member_count")
    selected = {}
    for items, size_key, pattern in (
            (evidence, "bytes", r"root-original-(?:[0-9]{2}\.txt|index\.json)"),
            (journals, "size", r"root-ledger-(?:private|[a-f0-9]{24})\.ledger\.txt")):
        for ref in items:
            fields = {"path", "sha256", size_key}
            if size_key == "size":
                fields.add("encoding")
            need(type(ref) is dict and set(ref) == fields, "reference_shape")
            name = ref["path"]
            need(type(name) is str and re.fullmatch(pattern, name)
                 and name not in selected, "member_name_or_duplicate")
            need(_number(ref[size_key]) and 0 < ref[size_key] <= 1_400_000
                 and _hash(ref["sha256"]), "reference_size_or_hash")
            if size_key == "size":
                need(ref["encoding"] == "unchanged-ndjson-bytes", "journal_encoding")
            raw = originals.get(name)
            need(type(raw) is bytes and len(raw) == ref[size_key]
                 and sha(raw) == ref["sha256"], "original_bytes")
            selected[name] = raw
    need(evidence[-1]["path"] == "root-original-index.json"
         and [r["path"] for r in evidence[:-1]] ==
             ["root-original-%02d.txt" % i for i in range(len(evidence)-1)], "chunk_order")
    index = _json(selected[evidence[-1]["path"]])
    need(type(index) is dict and set(index) == {"format", "members", "payload_sha256",
        "payload_bytes", "register_sha256", "binding_sha256"}
        and index["format"] == "admission-root-original-index-v1"
        and index["members"] == evidence[:-1], "index")
    payload = b"".join(selected[r["path"]] for r in evidence[:-1])
    need(0 < len(payload) <= 15_000_000 and type(index["payload_bytes"]) is int
         and len(payload) == index["payload_bytes"] and sha(payload) == index["payload_sha256"],
         "payload_digest")
    return _json(payload), index, {r["path"]: selected[r["path"]] for r in journals}


def _trusted(register, sources, binding):
    need(type(register) is dict and type(sources) is dict and sources
         and all(type(k) is str and k and _hash(v) for k, v in sources.items()), "trusted_sources")
    need(register.get("source_hashes") == sources, "source_binding")
    need(all(register.get(k) is True for k in ("bound_complete", "prefix_reserves_complete",
        "source_inventory_complete", "hosted_scope_complete"))
        and register.get("missing_costs") == [] and register.get("hosted_limit") == root.LIMIT,
        "trusted_bound_incomplete")
    unsigned = {k: v for k, v in register.items() if k != "full_register_sha256"}
    need(_hash(register.get("full_register_sha256"))
         and root.digest(unsigned) == register["full_register_sha256"], "trusted_digest")
    local, hosted = (register.get("total_local_ci_upper_bound"),
                     register.get("total_hosted_equivalent_upper_bound"))
    need(_number(local) and _number(hosted) and hosted <= root.LIMIT, "trusted_totals")
    _, _, program_local, program_hosted = root._program(register.get("executable_program"))
    need(local == program_local and hosted == program_hosted, "program_totals")
    need(type(binding) is dict and type(binding.get("run_id")) is str, "binding")
    try:
        run = uuid.UUID(binding["run_id"])
    except ValueError as error:
        raise root.RootBlocked("root_replay_binding") from error
    need(run.version == 4 and str(run) == binding["run_id"]
         and binding["run_id"] not in ("6f8c8909-9b79-4011-a9d1-db5e23c6b6c1",
                                      "11a909f4-7113-424a-aa4b-ce9964720a3e"), "fresh_case_binding")


class _Replay:
    """State reducer only: it cannot issue tickets or call runtime methods."""
    def __init__(self, journals, register_sha):
        self.journals, self.register_sha = journals, register_sha
        self.consumed = set()

    def journal(self, name, program, hosted_limit, depth=0):
        need(depth < 8 and name in self.journals and name not in self.consumed, "child_journal")
        self.consumed.add(name)
        nodes, next_node, local_bound, _ = root._program(program)
        events, unions, union_members, children = [], {}, {}, {}
        used = hosted = observed = 0
        stopped = closed = False
        pending = None
        previous = b""
        lines = self.journals[name].splitlines(keepends=True)
        need(lines and all(line.endswith(b"\n") for line in lines), "incomplete_journal")
        for sequence, line in enumerate(lines, 1):
            need(not closed, "record_after_close")
            value = _json(line)
            fields = {"sequence", "register_sha256", "previous_bytes_sha256", "event_ordinal",
                "reserved_consumed", "observed_sql_commands", "hosted_equivalent_reserved",
                "stopped", "closed", "event"}
            need(type(value) is dict and fields <= set(value)
                 and set(value) <= fields | {"numeric_union"}, "journal_shape")
            need(type(value["sequence"]) is int and value["sequence"] == sequence
                 and value["register_sha256"] == self.register_sha
                 and value["previous_bytes_sha256"] == sha(previous), "journal_chain")
            ordinal, event = value["event_ordinal"], value["event"]
            need(type(ordinal) is int and 0 <= ordinal <= len(events) and type(event) is dict,
                 "event_ordinal")
            need(type(value["closed"]) is bool and type(value["stopped"]) is bool, "state_type")
            is_close = value["closed"]
            if is_close:
                need(ordinal == len(events)-1 and root.digest(event) == root.digest(events[-1])
                     and next_node is None and pending is None, "close_before_terminal")
                closed = True
            elif ordinal == len(events):
                need(next_node is not None and pending is None, "dispatch_order")
                row = nodes[next_node]
                expected = {k: copy.deepcopy(v) for k, v in row.items() if k != "children"}
                if row["children"] is not None:
                    expected["child_program_sha256"] = root.digest(row["children"])
                expected.update(state="precharged", numeric_confirmed=False)
                need(root.digest(event) == root.digest(expected)
                     and (not stopped or row["safety_only"]), "precharge_instruction")
                used += row["units"]
                hosted += row["hosted_units"]
                need(used + row["reserve_after"] <= local_bound
                     and hosted + row["hosted_reserve_after"] <= hosted_limit, "prefix_capacity")
                pending = ordinal
                events.append(copy.deepcopy(event))
            else:
                old = events[ordinal]
                row = nodes[old["node_id"]]
                expected = copy.deepcopy(old)
                state = event.get("state")
                if old["state"] == "precharged":
                    need(pending == ordinal, "pending_identity")
                    if state in ("confirmed", "fault_numeric_confirmed"):
                        count = event.get("observed_sql_commands")
                        need(_number(count) and count <= row["units"], "numeric_count")
                        expected.update(state=state, numeric_confirmed=True, observed_sql_commands=count)
                        observed += count
                        if state == "fault_numeric_confirmed":
                            need(event.get("reason") in ("lost_response", "interrupted", "not_terminal",
                                                        "validation_failed"), "fault_reason")
                            expected["reason"] = event["reason"]
                            stopped = True
                            next_node = row["next_unknown"]
                        elif row["selection_cases"] is not None:
                            selection = event.get("cleanup_state")
                            target = row["selection_cases"].get(root.digest(selection))
                            need(type(selection) is dict and target is not None and count == 0
                                 and event.get("selected_node") == target, "cleanup_selection")
                            expected.update(cleanup_state=selection, selected_node=target)
                            next_node = target
                        else:
                            next_node = row["next_confirmed"]
                        if row["children"] is not None:
                            child_name = "root-ledger-" + root.digest([name, row["command_id"]])[:24] + ".ledger.txt"
                            child = self.journal(child_name, row["children"], row["hosted_units"], depth+1)
                            need(child["observed_sql_commands"] <= count
                                 and (not child["fault_retained"] or state == "fault_numeric_confirmed"),
                                 "child_numeric_coverage")
                            children[ordinal] = child
                    elif state in ("dispatched_measurement_pending", "fault_measurement_pending"):
                        partial = event.get("partial_observed_sql_commands")
                        need(row["defer"] and row["children"] is None and _number(partial)
                             and partial <= row["units"]-row["observation_units"], "defer_partition")
                        expected.update(state=state, partial_observed_sql_commands=partial)
                        observed += partial
                        failed = state == "fault_measurement_pending"
                        stopped = stopped or failed
                        next_node = row["next_unknown"] if failed else row["next_confirmed"]
                    else:
                        need(False, "unknown_or_failed_consumption")
                    pending = None
                elif old["state"] in ("dispatched_measurement_pending", "fault_measurement_pending"):
                    need(next_node is None and pending is None, "measurement_before_foreground_close")
                    if state == "confirmed":
                        count = event.get("observed_sql_commands")
                        need(row["observation_group"] is None and _number(count)
                             and count <= row["observation_units"], "deferred_numeric_count")
                        expected.update(state=state, numeric_confirmed=True, observed_sql_commands=count)
                        observed += count
                    elif state == "covered_by_numeric_union":
                        union = value.get("numeric_union")
                        need(type(union) is dict and set(union) == {"group", "command_ids",
                            "observed_sql_commands", "reserved_consumed", "per_request_attribution", "sha256"},
                            "union_shape")
                        union_sha = union["sha256"]
                        need(_hash(union_sha) and root.digest({k: v for k, v in union.items() if k != "sha256"})
                             == union_sha and row["observation_group"] == union["group"]
                             and union["group"] is not None and union["per_request_attribution"] is False,
                             "union_binding")
                        if union_sha not in unions:
                            members = [i for i, e in enumerate(events)
                                       if e["observation_group"] == union["group"]]
                            need(members and all(events[i]["state"] in
                                ("dispatched_measurement_pending", "fault_measurement_pending") for i in members),
                                "union_unknown_or_already_counted_partition")
                            ids = [events[i]["command_id"] for i in members]
                            need(type(union["command_ids"]) is list and len(set(ids)) == len(ids)
                                 and len(union["command_ids"]) == len(ids)
                                 and all(type(i) is str for i in union["command_ids"])
                                 and set(union["command_ids"]) == set(ids), "union_members")
                            reserved = sum(nodes[events[i]["node_id"]]["observation_units"] for i in members)
                            count = union["observed_sql_commands"]
                            need(_number(count) and count <= reserved and type(union["reserved_consumed"]) is int
                                 and union["reserved_consumed"] == reserved, "union_numeric_count")
                            unions[union_sha], union_members[union_sha] = copy.deepcopy(union), set(members)
                            observed += count
                        need(unions[union_sha] == union and ordinal in union_members[union_sha], "union_changed")
                        expected.update(state=state, numeric_confirmed=False, numeric_union_sha256=union_sha)
                    else:
                        need(False, "unknown_or_failed_measurement")
                else:
                    need(False, "duplicate_terminal_update")
                need(root.digest(event) == root.digest(expected), "event_changed")
                events[ordinal] = copy.deepcopy(event)
            if "numeric_union" in value:
                need(event.get("numeric_union_sha256") in unions
                     and unions[event["numeric_union_sha256"]] == value["numeric_union"], "unexpected_union")
            else:
                need("numeric_union_sha256" not in event, "missing_union")
            need(all(_number(value[k]) for k in ("reserved_consumed", "observed_sql_commands",
                 "hosted_equivalent_reserved")) and value["reserved_consumed"] == used
                 and value["observed_sql_commands"] == observed and value["hosted_equivalent_reserved"] == hosted
                 and value["stopped"] == stopped, "totals_or_fault_changed")
            previous += line
        need(closed and pending is None and next_node is None, "not_closed")
        need(all(e["state"] in ("confirmed", "fault_numeric_confirmed", "covered_by_numeric_union")
                 for e in events), "unsettled_measurement")
        for union_sha, members in union_members.items():
            need(all(events[i].get("numeric_union_sha256") == union_sha for i in members), "union_incomplete")
        need(observed <= used <= local_bound and hosted <= hosted_limit, "terminal_capacity")
        return dict(journal=name, local_source_bound=local_bound, reserved_consumed=used,
            observed_sql_commands=observed, hosted_equivalent_reserved=hosted, fault_retained=stopped,
            event_count=len(events), children=list(children.values()), numeric_unions=list(unions.values()))


def verify_exported_root(originals, *, trusted_root, expected_sources, binding, root_refs):
    """Replay unchanged member bytes; trusted_root must NOT come from originals.

    root_refs has evidence_refs (path/sha256/bytes) and journal_refs
    (path/sha256/size/encoding), as emitted by validate_terminal on the ROOT.
    Child-only references are insufficient. Unreferenced caller members are
    ignored, but all referenced journals must belong to the executed root tree.
    """
    _trusted(trusted_root, expected_sources, binding)
    value, index, journals = _originals(originals, root_refs)
    need(type(value) is dict and set(value) == {"format", "register", "program", "binding"}
         and value["format"] == "admission-root-original-evidence-v1"
         and root.digest(value["register"]) == root.digest(trusted_root)
         and root.digest(value["program"]) == root.digest(trusted_root["executable_program"])
         and root.digest(value["binding"]) == root.digest(binding) and index["binding_sha256"] == root.digest(binding)
         and index["register_sha256"] == trusted_root["full_register_sha256"], "original_trusted_binding")
    replay = _Replay(journals, trusted_root["full_register_sha256"])
    result = replay.journal("root-ledger-private.ledger.txt", value["program"], root.LIMIT)
    need(replay.consumed == set(journals), "unattached_journal")
    return dict(format="admission-root-archive-accounting-v1", status="NUMERIC_ACCOUNTING_REPLAYED",
        register_sha256=trusted_root["full_register_sha256"], binding=copy.deepcopy(binding),
        source_hashes=copy.deepcopy(expected_sources), root=result, journal_count=len(journals),
        original_refs=copy.deepcopy(root_refs), covered_children_not_added=True,
        observed_execution_independently_proven=False, source_semantics_independently_proven=False,
        runtime_admitted=False, full_chain_admission=False, hosted_admitted=False)
