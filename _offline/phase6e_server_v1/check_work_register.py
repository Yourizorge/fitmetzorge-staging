"""Executable dependency/path check, not a feature-completion score."""
import json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
def check():
    value=json.loads((HERE/'work_register.json').read_text());items=value['functions'];by={x['id']:x for x in items}
    assert len(by)==len(items) and value['full_day21'] is False
    def visit(key,chain):
        assert key not in chain
        item=by[key]
        for field in ('behavior','remaining','gate','state'):assert item[field]
        for file in item['sources']+item['tests']:
            assert '..' not in pathlib.Path(file).parts and (HERE/file).is_file()
        for dep in item['depends']:visit(dep,chain+[key])
    for key in by:visit(key,[])
    return {'register':'VALID_NOT_FEATURE_PASS','functions':len(by),'hosted':value['hosted11'],
            'states':{k:v['state'] for k,v in by.items()},'external_ai_enabled':False}
if __name__=='__main__':print(json.dumps(check(),indent=2))
