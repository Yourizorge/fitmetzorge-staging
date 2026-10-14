"""Reject credential-shaped source, except one byte-pinned parser test literal."""
import hashlib,re

def check(name,raw):
    found=re.findall(rb'(?:sbp_|sb_secret_|gh[pousr]_)[A-Za-z0-9_-]{16,}',raw)
    if not found:return
    fixed=b'sb'+b'p_synthetic_validation_only'
    if (name=='_offline/phase6e11/access_v1/cli_check.py' and found==[fixed]
        and hashlib.sha256(raw).hexdigest()=='f4f0293cc033cc3a5e2e5762ea3ccc110febc0ba5415cfdbf1ef782ddb778f0a'):
        return
    raise ValueError('source_credential_pattern')
