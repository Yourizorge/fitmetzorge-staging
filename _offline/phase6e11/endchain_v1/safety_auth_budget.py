"""Pure command/state contract shared by register, meter and failure executor."""
ROLES=('a_member','a_trainer','b_member')
MANAGED_PER_ROLE=10
NATIVE_PER_ROLE=6
NATIVE_FALLBACK=12
RESERVE=3*(MANAGED_PER_ROLE+NATIVE_PER_ROLE)+NATIVE_FALLBACK


def labels():
    out=[]
    for role in ROLES:
        out.append({'action':'auth_logout_'+role,'sql':NATIVE_PER_ROLE,'kind':'native'})
        out.append({'action':'auth_logout_managed_'+role,'sql':MANAGED_PER_ROLE,'kind':'managed_auth'})
    return out+[{'action':'auth_native_fallback','sql':NATIVE_FALLBACK,'kind':'native'}]


def reserve_required(used,normal_remaining,existing_safety,auth_maybe_live):
    return used+max(normal_remaining,existing_safety+(RESERVE if auth_maybe_live else 0))


def auth_state_before(maybe_live,operation):
    return maybe_live or operation=='issue'


def auth_state_after(maybe_live,*,confirmed,exact_three_zero,mint_terminal):
    return maybe_live and not (confirmed is True and exact_three_zero is True and mint_terminal is True)
