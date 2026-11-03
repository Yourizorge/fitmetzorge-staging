"""Keep original failures primary when durable evidence or closure also fails."""
import pathlib
import re


def budget_diagnostic(error):
    """Allowlisted source locations only: no exception message, locals or OS path."""
    stages = {'assemble', 'actual_receipts', 'normal_reconciliation',
              'current_reconciliation', 'package', 'save'}
    files = {'admission_budget.py', 'admission_budget_register.py',
             'admission_budget_receipts.py', 'admission_budget_graph.py'}
    value = {'stage': getattr(error, 'admission_budget_stage', None)}
    if value['stage'] not in stages:
        value['stage'] = 'unclassified'
    frames = []
    frame = error.__traceback__
    while frame is not None:
        code = frame.tb_frame.f_code
        name = pathlib.Path(code.co_filename).name
        if name in files:
            function = code.co_name
            frames.append({'file': name, 'line': frame.tb_lineno,
                           'function': function if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', function)
                           else 'expression'})
        frame = frame.tb_next
    value['source_frames'] = frames[-16:]
    return value


def secondary(gate, phase, error, primary):
    value={'phase':phase,'primary_class':type(primary).__name__ if primary else None,
           'secondary_class':type(error).__name__,'status':'NO_GO'}
    if phase == 'budget_packaging':
        value['diagnostic'] = budget_diagnostic(error)
    if not hasattr(gate,'result'):gate.result={}
    gate.result.setdefault('admission_secondary_failures',[]).append(value)
    if primary is not None:
        prior=getattr(primary,'admission_secondary_failures',[])
        primary.admission_secondary_failures=[*prior,value]
    return value


def save_final(gate, name, value, primary=None):
    try:gate.save(name,value)
    except Exception as error:
        secondary(gate,'receipt_storage',error,primary)
        if primary is None:raise


def package_journal(gate, journal, publish, primary=None):
    from admission_journal import verify
    import json
    try:
        index=journal.seal()
        result=verify(index,lambda name:json.loads((gate.out/name).read_bytes()))
        publish(journal.prefix+'-verified.json',result)
    except Exception as error:
        secondary(gate,'journal_packaging',error,primary)
        if primary is None:raise
