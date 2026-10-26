"""Pure selected-slice action guard. No files, generated JSON, SQL or admission.

Call only with role/route/workspace kind obtained from verified server state.
None is not a selection: the local Application decides whether to retain its
existing bulk mode by omitting this optional guard. This grants no hosted access.
"""
from types import MappingProxyType

FORBIDDEN = ('record', 'finish_workout', 'finish_day')

# These are selections from the existing application, not new feature rules.
SLICES = (
    dict(id='registration12', title='Minimal historical registration12',
         functions=['registration12'], adapter='RegistrationStore',
         entries=['registration12.cjs', 'registration_store.py', 'registration_transport.py', 'registration_proof.py'],
         actions={'member': ['register12', 'revoke']}, edit_domains=[],
         state=['records', 'events', 'revision', 'consent'],
         invariants=['fixture, source and original snapshot immutable', 'correction appends a record version',
                     'missing/null and zero distinct; independent RIR/RPE', 'no start12/finish12, plan apply or outbox'],
         node=['registration12.test.cjs'],
         python=['test_registration_scope.py', 'test_registration_release.py', 'test_registration_accounting.py', 'test_receipt_accounting.py'],
         integration=['registration_database.py', 'registration_browser.cjs', 'registration_proof.py'],
         checks=['save/correct/reload/relogin', 'expired session, other workspace, wrong actor',
                 'duplicate payload conflict, CAS, rollback after each write', '22 exact transport pairs on A/B'],
         rollback='Close minimal entry and exact synthetic subjects; preserve original snapshots, revisions and audit.'),
    dict(id='signals13_14', title='Source-bound signals and corrections',
         functions=['today_progress', 'save_recovery'], adapter='Store',
         entries=['domain.cjs', 'windows.cjs'],
         actions={'member': ['compare_window', 'health', 'revoke']}, edit_domains=[],
         state=['comparison', 'comparisonHistory', 'sourceRevision', 'sourceGeneration', 'sourceHash',
                'review', 'proposal', 'member', 'trainer', 'notices', 'facts', 'status', 'reason',
                'healthLatch', 'health', 'recovery.health', 'consent', 'revision', 'audit'],
         invariants=['complete comparable version-bound windows only', 'correction invalidates both approvals',
                     'historical register12 correction uses slice1; current record actions remain21-off'],
         node=['domain.test.cjs', 'windows.test.cjs'], python=['test_outbox.py'],
         integration=['database_tests.py', 'browser_checks.cjs'],
         checks=['24 complete version-bound window rows', 'missing/conflicting/duplicate/stale bundle',
                 'signal deduplication and supersession; health never grants resumption'],
         rollback='Disable comparison/signal processing; retain registrations, window revisions and prior notices.'),
    dict(id='intake15', title='Route B intake and plan proposal',
         functions=['intake', 'plans'], adapter='Store',
         entries=['panels.js', 'domain.cjs'],
         actions={'member': ['intake', 'build', 'revoke']}, edit_domains=[],
         state=['pair', 'intakeHistory', 'healthLatch', 'consent', 'sourceRevision', 'sourceGeneration',
                'sourceHash', 'comparison', 'facts', 'review', 'proposal', 'member', 'trainer', 'notices',
                'status', 'reason', 'revision', 'audit'],
         invariants=['B only; Route A contract unchanged', 'frozen catalogue/intake validators',
                     'build creates a proposal, not an applied plan; application is slice5'],
         node=['domain.test.cjs', 'presentation.test.cjs', 'windows.test.cjs'], python=['test_outbox.py'],
         integration=['database_tests.py', 'composed_browser.cjs'],
         checks=['catalogue expiry, allergy conflict, missing consent', 'old intake preserved and approvals invalidated',
                 'equipment, days, frequency, time, exclusions; B has no trainer step'],
         rollback='Close new intake/build actions; retain previous intake, catalogue and plan versions.'),
    dict(id='plans16_17', title='Training and nutrition plan editing',
         functions=['plans'], adapter='Store', entries=['presentation.cjs', 'panels.js', 'domain.cjs'],
         actions={'member': ['edit', 'revoke']},
         edit_domains=['training_day', 'training_exercise', 'training_session', 'nutrition_portion', 'nutrition_item', 'nutrition_moment'],
         state=['review', 'proposal', 'member', 'trainer', 'sourceRevision', 'sourceHash', 'comparison', 'facts',
                'notices', 'status', 'reason', 'consent', 'sourceGeneration', 'revision', 'audit'],
         invariants=['B edits use exact exercise/product and catalogue versions', 'A has no expanded trainer prescription scope',
                     'edits propose; slice5 applies', 'planned totals never presented as consumed'],
         node=['domain.test.cjs', 'presentation.test.cjs', 'windows.test.cjs'], python=['test_outbox.py'],
         integration=['database_tests.py', 'composed_browser.cjs'],
         checks=['sets/reps/rest/RIR/RPE independently validated', 'food version and portion bounds',
                 'missing versus zero; immutable snapshots and rejected out-of-catalogue edits'],
         rollback='Close plan editing; retain every old snapshot. Never rewrite previously approved plans.'),
    dict(id='review18', title='Joint review and separate application',
         functions=['review'], adapter='Store', entries=['domain.cjs', 'store.py'],
         actions={'member': ['confirm', 'apply', 'reject', 'restore', 'revoke'], 'trainer': ['approve', 'block']}, edit_domains=[],
         state=['review', 'status', 'reason', 'active', 'history', 'records', 'closed', 'dayClose', 'recordHistory',
                'consent', 'sourceRevision', 'sourceGeneration', 'sourceHash', 'comparison', 'facts', 'proposal',
                'member', 'trainer', 'notices', 'revision', 'audit'],
         invariants=['A member then linked trainer; separate apply', 'B member then separate apply, no trainer',
                     'restore is a new proposal requiring fresh approvals', 'plan slots are not actual21 registrations'],
         node=['domain.test.cjs', 'windows.test.cjs'], python=['test_outbox.py', 'test_protocol.py'],
         integration=['database_tests.py', 'browser_checks.cjs', 'composed_browser.cjs'],
         checks=['CAS conflict, duplicate/rebound request, source invalidation', 'rollback after head/revision/receipt/outbox',
                 'training-only trainer projection; uncertain commit reconciles exact request'],
         rollback='Close apply/restore; keep active and historical plans. Restore only as a new fully approved version.'),
    dict(id='recovery19_today20', title='Recovery, check-in and Today',
         functions=['recovery', 'today_progress'], adapter='Store',
         entries=['windows.cjs', 'planning.py', 'outbox.py', 'presentation.cjs', 'ui.js'],
         actions={'member': ['recovery', 'complete', 'compare_window', 'health', 'edit', 'notice_seen', 'revoke']}, edit_domains=['time'],
         state=['recovery', 'recoveryHistory', 'completion', 'comparison', 'comparisonHistory', 'healthLatch', 'health',
                'sourceRevision', 'sourceGeneration', 'sourceHash', 'review', 'proposal', 'member', 'trainer',
                'notices', 'facts', 'status', 'reason', 'consent', 'revision', 'audit'],
         invariants=['server clock and explicit approved time, no background scheduler', 'outbox is in-app only, no real push',
                     'notice_seen changes outbox/receipt without new plan revision', 'cadence apply still requires slice5'],
         node=['domain.test.cjs', 'windows.test.cjs', 'presentation.test.cjs'], python=['test_outbox.py', 'test_planning.py'],
         integration=['database_tests.py', 'composed_browser.cjs'],
         checks=['DST fold/gap, timezone, missing windows', 'outbox deduplication/withdrawal/expiry/history',
                 'lost response after commit, same request reconciliation; no duplicate event'],
         rollback='Disable new recovery/notice processing and delivery; retain event histories and never replay undelivered events as new.'),
    dict(id='workout12', title='Composed historical workout controls',
         functions=['workout12'], adapter='RegistrationStore',
         entries=['workout12.cjs', 'composed_store.py', 'registration_store.py'],
         actions={'member': ['start12', 'register12', 'finish12', 'revoke']}, edit_domains=[],
         state=['session12', 'records', 'events', 'revision', 'consent'],
         invariants=['same Auth object; historical workspace distinct from primary workspace', 'explicit start and finish',
                     'partial remains partial; historical snapshot never becomes current plan', 'journey=True is excluded from slice1'],
         node=['registration12.test.cjs', 'workout12.test.cjs'], python=['test_protocol.py'],
         integration=['database_tests.py', 'composed_browser.cjs'],
         checks=['no register before start, no duplicate finish', 'source/snapshot binding, null/zero, immutable closures',
                 'reload/relogin, cross-workspace and account-switch denial'],
         rollback='Disable journey mount/start/finish only; keep minimal registration and all previous closures.'),
    dict(id='preferences', title='Preferences and readable units',
         functions=['preferences'], adapter='Store', entries=['presentation.cjs', 'display.js', 'domain.cjs', 'ui.js'],
         actions={'member': ['preferences', 'revoke']}, edit_domains=[],
         state=['preferences', 'revision', 'audit', 'consent', 'sourceRevision', 'sourceGeneration',
                'sourceHash', 'review', 'proposal', 'member', 'trainer', 'comparison', 'facts', 'notices', 'status', 'reason'],
         invariants=['preferences action only changes preferences/revision/audit; revoke has separate invalidation writes',
                     'original value/unit and physical plan unchanged', 'display conversion is approximate, never stored conversion'],
         node=['presentation.test.cjs', 'display.test.cjs', 'domain.test.cjs', 'windows.test.cjs'], python=['test_outbox.py'],
         integration=['database_tests.py', 'composed_browser.cjs'],
         checks=['NL/EN/DE, light/dark, metric/imperial, reload', 'preferences preserve source/plan/approvals',
                 'no-op preference receipt; expiry/withdrawal can still update existing outbox'],
         rollback='Close preference writes; preserve original source values and units without conversion.'),
)

class SelectionDenied(ValueError):
    pass


# Freeze the enforcement policy independently of the builder's descriptive data.
_POLICIES = MappingProxyType({
    spec['id']: (
        MappingProxyType({role: frozenset(actions) for role, actions in spec['actions'].items()}),
        frozenset(spec['edit_domains']),
        frozenset(('B',) if spec['id'] in ('intake15', 'plans16_17') else ('A', 'B')),
        'registration12' if spec['id'] in ('registration12', 'workout12') else 'primary',
    ) for spec in SLICES
})


def _policy(slice_id):
    if type(slice_id) is not str or slice_id not in _POLICIES:
        raise SelectionDenied('release_slice_unknown')
    return _POLICIES[slice_id]


def validate_slice(slice_id):
    """Validate trusted operator configuration; None retains local bulk mode."""
    if slice_id is None:
        return None
    _policy(slice_id)
    return slice_id


def _context(policy, role, route, workspace_kind):
    actions, _, routes, kind = policy
    if type(role) is not str or role not in actions:
        raise SelectionDenied('release_slice_role')
    if workspace_kind != kind:
        raise SelectionDenied('release_slice_workspace')
    # Historical read views do not expose a route. Both routes have the same
    # member-only historical policy; no primary/trainer access follows from None.
    if not (kind == 'registration12' and route is None):
        if type(route) is not str or route not in routes:
            raise SelectionDenied('release_slice_route')
    if role == 'trainer' and route != 'A':
        raise SelectionDenied('release_slice_route')


def require_action(slice_id, request, *, role, route, workspace_kind):
    """Raise SelectionDenied before dispatch; existing payload/Auth/CAS checks remain."""
    policy = _policy(slice_id)
    _context(policy, role, route, workspace_kind)
    if type(request) is not dict or set(request) != {'action', 'data'}:
        raise SelectionDenied('release_request_shape')
    action, data = request['action'], request['data']
    if type(action) is not str or type(data) is not dict:
        raise SelectionDenied('release_request_shape')
    if action in FORBIDDEN or action not in policy[0][role]:
        raise SelectionDenied('release_slice_action')
    if action == 'edit':
        if set(data) != {'domain', 'value'} or type(data['domain']) is not str:
            raise SelectionDenied('release_edit_shape')
        if data['domain'] not in policy[1]:
            raise SelectionDenied('release_edit_domain')
    # Field values, version/source bindings, consent and current session are
    # deliberately validated by the existing Store/domain after this selection.
    return None


def selection_allows(packet, action, role, route, domain=None):
    """Compatibility predicate for packet inspection; canonical ID selects policy."""
    try:
        if type(packet) is not dict:
            return False
        slice_id = packet.get('id')
        policy = _policy(slice_id)
        data = {'domain': domain, 'value': None} if action == 'edit' else {}
        require_action(slice_id, {'action': action, 'data': data},
                       role=role, route=route, workspace_kind=policy[3])
        return True
    except SelectionDenied:
        return False
