"""Explicit owner-approved native-adapter retry, separate from consumed attempts."""
import hashlib,json

PRIOR='phase6e11-auth-metadata-hosted-15d85ca72ce2405b93c5918c1801b028'
MARKER='phase6e11-auth-metadata-owner-native-once.json'

def validate(result,audit,closed,metadata_removed,guard_removed):
    if result.get('status')!='NO_GO' or result.get('commands')!=95 or result.get('combined_commands')!=103 or result.get('auth_calls')!=0 or result.get('application_writes')!=0:
        raise ValueError('owner_retry_prior_mismatch')
    if not result.get('jit_revoked') or closed.get('remaining_mappings')!=0 or not closed.get('disabled'):
        raise ValueError('owner_retry_prior_access')
    if audit.get('status')!='NO_GO' or audit.get('error_class')!='Stop' or not audit.get('metadata_removed'):
        raise ValueError('owner_retry_prior_action')
    if not metadata_removed.get('existing_equal') or metadata_removed.get('own_additions')!=0 or not guard_removed.get('existing_objects_equal') or guard_removed.get('own_additions')!=0:
        raise ValueError('owner_retry_prior_cleanup')
    return {'approval':'owner_native_adapter_once_2026_10_12','prior_run':PRIOR,
            'historical_commands':103,'prior_commands':0,'max_seconds':180,
            'max_commands':128,'safety_reserved':40,'automatic_retries':0,
            'auth_calls':0,'workflow_writes':0}

def admission(root):
    folder=root/'supabase/.temp'/PRIOR
    names=['result','audit-result','closed','metadata-removal-pair','removal-pair']
    raw={n:(folder/(n+'.json')).read_bytes() for n in names}
    value=validate(*(json.loads(raw[n]) for n in names))
    value['historical_evidence_sha256']={n:hashlib.sha256(b).hexdigest() for n,b in raw.items()}
    return value
