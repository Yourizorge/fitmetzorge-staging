"""Keep original failures primary when durable evidence or closure also fails."""


def secondary(gate, phase, error, primary):
    value={'phase':phase,'primary_class':type(primary).__name__ if primary else None,
           'secondary_class':type(error).__name__,'status':'NO_GO'}
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
