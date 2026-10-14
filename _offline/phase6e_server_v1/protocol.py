"""Explicit transaction accounting; never logs SQL parameters or row contents."""
import contextlib,hashlib,time,uuid

class Session:
    def __init__(self,connection,observer,operation):
        self.connection=connection;self.observer=observer;self.operation=operation
        self.call_id=str(uuid.uuid4());self.ordinal=0
    def execute(self,query,parameters=None):
        self.ordinal+=1
        event={'call_id':self.call_id,'operation':self.operation,'ordinal':self.ordinal,
            'template_sha256':hashlib.sha256(query.encode()).hexdigest(),'confirmed':False}
        started=time.monotonic()
        if self.observer:self.observer({**event,'phase':'started'})
        try:
            result=self.connection.execute(query,parameters)
            event['confirmed']=True
            return result
        finally:
            if self.observer:self.observer({**event,'phase':'completed','duration_ms':round((time.monotonic()-started)*1000)})
    @contextlib.contextmanager
    def transaction(self):
        opened=False
        try:
            opened=True;self.execute('BEGIN');yield self
            self.execute('COMMIT');opened=False
        except Exception:
            if opened:
                try:self.execute('ROLLBACK')
                except Exception:pass
            raise

@contextlib.contextmanager
def transaction(connect,observer,operation):
    connection=connect();session=Session(connection,observer,operation);opened=False
    try:
        opened=True;session.execute('BEGIN')
        yield session
        session.execute('COMMIT');opened=False
    except Exception:
        if opened:
            try:session.execute('ROLLBACK')
            except Exception:pass
        raise
    finally:connection.close()
