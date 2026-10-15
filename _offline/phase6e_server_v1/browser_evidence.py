"""Retain bounded browser failure metadata, never raw process output."""
import json,re

def result(process):
    try:
        value=json.loads(process.stdout)
        if isinstance(value,dict) and value.get('status') in ('PASS','FAIL'):
            return value
    except (ValueError,TypeError):pass
    failure={'status':'FAIL','exit_code':process.returncode,
             'stage':'unreported','error':'browser_output_missing_or_invalid'}
    try:
        value=json.loads(process.stderr)
        message=value.get('error','') if isinstance(value,dict) else ''
        stage,detail=message.split(': ',1)
        if re.fullmatch(r'[a-z][a-z0-9_]{0,79}',stage):failure['stage']=stage
        first=detail.splitlines()[0]
        if re.fullmatch(r'[a-z][a-z0-9_]{0,119}',first):failure['error']=first
        elif re.fullmatch(r'[a-zA-Z.]+: Timeout [0-9]{1,6}ms exceeded\.',first):
            failure['error']='browser_timeout'
            failure['operation']=first.split(':')[0]
    except (ValueError,TypeError,AttributeError,IndexError):pass
    return failure
