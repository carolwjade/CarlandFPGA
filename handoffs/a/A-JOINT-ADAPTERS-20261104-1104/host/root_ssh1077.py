"""Root-owned one-shot private-input seam around the reviewed B SSH client.

Import/construct is inert. Root supplies trusted argv, reviewed B class, process
factory, one private bytes-line supplier and an exclusively owned stderr sink.
No credential path, password logging/hash, reconnect, replay, or board loading.
"""
import copy
import subprocess
import threading
import time

CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'


class CredentialInputError(RuntimeError):
    pass


class TransportCloseError(RuntimeError):
    pass


class RootSshDisplayClient:
    """One IO owner; preserves B session, reader and relative-deadline logic.

    credential_supplier() returns exactly one nonempty bytes line ending in LF.
    It is called once, only after this explicit open launches the one process.
    The bytes go directly into the process stdin binary buffer and are not
    stored in this adapter, converted to text, hashed, or reported.

    stderr_sink is a new file already opened by Root; ownership transfers here.
    Child stderr redirects directly to that file, avoiding an undrained pipe.
    Closing awaits actual process exit/reader completion without a new timeout
    or terminate/kill. A failed wait leaves its actual outcome marked unknown.
    """
    def __init__(self,ssh_client_class,argv,*,credential_supplier,process_factory,
                 stderr_sink,timeout=1.5,seed_ready_request_id=True,on_event=None):
        if not callable(ssh_client_class) or not callable(credential_supplier) or not callable(process_factory):
            raise ValueError('ROOT_REVIEWED_FACTORIES_REQUIRED')
        if type(seed_ready_request_id) is not bool:raise ValueError('EXPLICIT_REQUEST_SEED_POLICY')
        if on_event is not None and not callable(on_event):raise ValueError('EVENT_CALLBACK')
        if not callable(getattr(stderr_sink,'close',None)):raise ValueError('ROOT_OWNED_STDERR_SINK')
        self._client=ssh_client_class(argv,timeout=timeout,keepalive=False)
        if self._client.keepalive is not False:raise ValueError('BACKGROUND_KEEPALIVE_DISABLED')
        self._credential_supplier,self._process_factory=credential_supplier,process_factory
        self._stderr_sink,self._on_event=stderr_sink,on_event
        self._seed_request=seed_ready_request_id
        self._owner=threading.get_ident();self._attempted=False;self._opened=False;self._closing=False
        self._welcome=None;self._stop_attempted=False
        self._audit=dict(open_attempted=False,opened=False,credential_written=False,
                         stop_attempted=False,stop_reply=None,stop_error_type=None,
                         open_error_type=None,open_error_phase=None,process_id=None,
                         stdin_closed=False,wait_completed=False,returncode=None,
                         reader_joined=False,stdout_closed=False,stderr_closed=False,
                         transport_outcome='not_started',close_errors=[],reconnect=False)

    @property
    def keepalive(self):return self._client.keepalive

    @property
    def failed(self):return self._client.failed

    @property
    def welcome(self):return copy.deepcopy(self._welcome)

    @property
    def audit(self):return copy.deepcopy(self._audit)

    def _owned(self):
        if threading.get_ident()!=self._owner:raise RuntimeError('ONE_HOST_SSH_IO_OWNER')

    def _event(self,event,**fields):
        if self._on_event is not None:self._on_event(dict(event=event,**copy.deepcopy(fields)))

    def _input_once(self):
        line=None
        try:
            line=self._credential_supplier()
            if (type(line) is not bytes or not 2<=len(line)<=4096 or not line.endswith(b'\n')
                    or b'\n' in line[:-1] or b'\r' in line or b'\0' in line):
                raise ValueError('ONE_PRIVATE_LF_BYTES_LINE_REQUIRED')
            stream=self._client.process.stdin.buffer
            written=stream.write(line)
            if written!=len(line):raise OSError('PRIVATE_INPUT_WRITE_INCOMPLETE_NO_RETRY')
            stream.flush()
            self._audit['credential_written']=True
        except BaseException as error:
            # Supplier/stream exception text might contain its input. Never
            # propagate/log that text through HostFollower's ordinary errors.
            raise CredentialInputError('Private input failed ('+type(error).__name__+'); no replay') from None
        finally:
            line=None

    def open(self):
        self._owned()
        if self._attempted or self._closing:raise RuntimeError('ONE_OPEN_ATTEMPT_NO_RECONNECT')
        self._attempted=True;self._audit['open_attempted']=True
        phase='process_start'
        try:
            client=self._client
            if client.process is not None:raise RuntimeError('REVIEWED_CLIENT_ALREADY_OPEN')
            client.process=self._process_factory(client.argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=self._stderr_sink,text=True,encoding='utf8',bufsize=1,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self._audit['process_id']=getattr(client.process,'pid',None)
            self._audit['transport_outcome']='started'
            self._event('ssh_process_started',process_id=self._audit['process_id'])
            phase='private_input'
            self._input_once()
            # Keep B's exact bounded-line reader and existing handshake timeout.
            phase='ready_handshake'
            client.reader=threading.Thread(target=client._read,daemon=True)
            client.reader.start()
            ready=client._receive(45)
            if (type(ready) is not dict or ready.get('event')!='ready'
                    or type(ready.get('session')) is not str or not ready['session']
                    or type(ready.get('clock_ms')) is not int or not 0<=ready['clock_ms']<=2**53):
                raise RuntimeError('ACTUAL_READY_SESSION_CLOCK_REQUIRED')
            request_id=ready.get('request_id',0)
            if type(request_id) is not int or not 0<=request_id<=0xffffffff:
                raise RuntimeError('ACTUAL_READY_REQUEST_ID_REQUIRED')
            client.session_id=ready['session']
            client.board_ms,client.started=ready['clock_ms'],time.monotonic()
            if self._seed_request:client.rid=request_id
            self._welcome=copy.deepcopy(ready)
            self._opened=True;self._audit['opened']=True
            self._event('ssh_welcome',welcome=ready,seeded_request_id=client.rid,
                        physical_readiness='status_is_original_remote_record')
            return ready
        except BaseException as error:
            self._client.failed=True  # Actual failed open, matching B semantics.
            self._audit.update(open_error_type=type(error).__name__,open_error_phase=phase)
            try:self._event('ssh_open_failed',error_type=type(error).__name__,phase=phase,retry=False)
            except BaseException:pass
            # Never send a guessed STOP before a successful handshake. EOF is
            # consumed by the original remote finally path when it is alive.
            try:self._close_transport()
            except BaseException:pass
            raise

    def _live(self):
        self._owned()
        if not self._opened or self._closing or self._client.closed.is_set() or self._client.failed:
            raise RuntimeError('SSH_SESSION_NOT_LIVE_NO_REPLAY')
        if self._stop_attempted:raise RuntimeError('SSH_TERMINAL_STOP_ALREADY_ATTEMPTED')

    def _actual_call(self,method,*args,**kwargs):
        self._live()
        op=args[0].get('op') if method=='call' and args and type(args[0]) is dict else method
        if op=='stop':
            self._stop_attempted=True;self._audit['stop_attempted']=True
        try:
            reply=getattr(self._client,method)(*args,**kwargs)
            if op=='stop':self._audit['stop_reply']=copy.deepcopy(reply)
            self._event('ssh_actual_reply',op=op,reply=reply)
            return reply
        except BaseException as error:
            if op=='stop':self._audit['stop_error_type']=type(error).__name__
            try:self._event('ssh_command_failed',op=op,error_type=type(error).__name__,retry=False)
            except BaseException:pass
            raise

    def call(self,command):return self._actual_call('call',command)
    def pose(self,*args,**kwargs):return self._actual_call('pose',*args,**kwargs)
    def motor(self,speed_pct):return self._actual_call('motor',speed_pct)

    def close(self,*,stop_already_attempted=False):
        self._owned()
        if type(stop_already_attempted) is not bool:raise ValueError('EXPLICIT_STOP_HISTORY')
        if self._closing:return self.audit
        if (not stop_already_attempted and not self._stop_attempted and self._opened
                and not self._client.failed and not self._client.closed.is_set()):
            try:self.call({'op':'stop'})
            except BaseException:pass
        return self._close_transport()

    def _close_transport(self):
        self._owned()
        if self._closing:return self.audit
        self._closing=True;client=self._client;process=client.process
        client.closed.set()  # Terminal client state, not a claim of process exit.
        errors=self._audit['close_errors']
        if process is not None:
            try:
                process.stdin.close();self._audit['stdin_closed']=True
            except BaseException as error:errors.append(dict(phase='stdin_eof',error_type=type(error).__name__))
            try:
                result=process.wait()  # No invented fixed timeout or process kill.
                self._audit.update(wait_completed=True,returncode=result,transport_outcome='process_exited')
            except BaseException as error:
                errors.append(dict(phase='process_wait',error_type=type(error).__name__))
                self._audit['transport_outcome']='unknown_process_outcome'
            if self._audit['wait_completed']:
                reader=getattr(client,'reader',None)
                try:
                    if reader is not None:reader.join()
                    self._audit['reader_joined']=reader is None or not reader.is_alive()
                except BaseException as error:errors.append(dict(phase='reader_join',error_type=type(error).__name__))
                if self._audit['reader_joined']:
                    try:process.stdout.close();self._audit['stdout_closed']=True
                    except BaseException as error:errors.append(dict(phase='stdout_close',error_type=type(error).__name__))
        else:self._audit['transport_outcome']='not_started_closed'
        if process is None or self._audit['wait_completed']:
            try:self._stderr_sink.close();self._audit['stderr_closed']=True
            except BaseException as error:errors.append(dict(phase='stderr_close',error_type=type(error).__name__))
        try:self._event('ssh_transport_closed',audit=self.audit)
        except BaseException as error:errors.append(dict(phase='close_event',error_type=type(error).__name__))
        if errors:raise TransportCloseError('SSH close incomplete; inspect actual close audit; no replay')
        return self.audit


def close_root_ssh_client(raw,*,stop_already_attempted):
    """Direct HostFollower1060 close_client callback, on the same IO thread."""
    return raw.close(stop_already_attempted=stop_already_attempted)
