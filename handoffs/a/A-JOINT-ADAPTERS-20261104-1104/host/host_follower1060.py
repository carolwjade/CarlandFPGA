"""PC-side latest-state physical follower, inert until Root calls start().

Root injects already reviewed B API classes and an opened-client factory.
No native RPC, credentials, SSH/process creation, PYNQ, or clock translation.
This module consumes actual own-pose; it has no simulation control authority.
"""
import copy
import dataclasses
import threading
import time

CONTRACT_SHA256='2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d'


class _ObservedClient:
    """All B calls originate on one worker; replies remain actual unedited data."""
    def __init__(self, owner, adapter):
        self.owner,self.adapter=owner,adapter
        self.thread_id=threading.get_ident()
        self.stop_attempted=False

    def _call(self, method, *args, **kwargs):
        if threading.get_ident()!=self.thread_id:raise RuntimeError('ONE_PHYSICAL_IO_THREAD')
        if method=='stop':
            if self.stop_attempted:raise RuntimeError('DUPLICATE_FOLLOWER_STOP_PREVENTED')
            self.stop_attempted=True
            self.owner._set(stop_attempted=True)
        else:
            self.owner._positive_guard()
        reply=getattr(self.adapter,method)(*args,**kwargs)
        self.owner._set(last_actual_reply=copy.deepcopy(reply))
        self.owner._emit('client_reply',method=method,reply=copy.deepcopy(reply))
        return reply

    def pose(self,*args,**kwargs):return self._call('pose',*args,**kwargs)
    def motor(self,speed_pct):return self._call('motor',speed_pct)
    def keepalive(self):return self._call('keepalive')
    def stop(self):return self._call('stop')


class HostFollower:
    """LatestDisplayMailbox -> B mapper/follower, all on this same QPC host.

    client_factory() must create AND open Root's reviewed SshDisplayClient with
    keepalive=False, returning it on the IO thread. close_client, if supplied,
    receives that raw client and stop_already_attempted=bool. It owns transport
    EOF/wait policy and must never replay a command of unknown outcome.

    Without close_client the frozen client.close() is used unchanged. Its extra
    normal-close STOP RPC is served from B's STOP cache; it is not a second
    device command. No internal failed flag is fabricated to suppress that RPC.

    on_event runs on the IO thread and must be nonblocking. 'client_reply'
    contains actual raw client records, including rejected status values.
    Derived target events are labelled separately and are not measured feedback.
    """
    def __init__(self,mailbox,*,api,client_factory,run_id,source,reference_xyzw,
                 limits,motor_enabled=False,close_client=None,on_event=None):
        if type(run_id) is not str or not run_id or len(run_id)>128 or not run_id.isascii():raise ValueError('EXPLICIT_RUN_ID')
        if source not in ('PC_DIRECT','FPGA_OUTPUT'):raise ValueError('EXPLICIT_ACTUAL_SOURCE')
        if mailbox.run_id!=run_id or mailbox.source!=source:raise ValueError('MAILBOX_RUN_SOURCE_BINDING')
        if type(motor_enabled) is not bool:raise ValueError('EXPLICIT_MOTOR_ENABLE')
        if not callable(client_factory) or close_client is not None and not callable(close_client):raise ValueError('ROOT_CLIENT_CALLBACKS')
        if on_event is not None and not callable(on_event):raise ValueError('EVENT_CALLBACK')
        for name in ('FollowMapper','Follower','SshClientAdapter'):
            if not callable(getattr(api,name,None)):raise ValueError('ROOT_INJECTED_B_API_'+name)
        self.mailbox,self.api,self.client_factory=mailbox,api,client_factory
        self.run_id,self.source,self.reference_xyzw=run_id,source,copy.deepcopy(reference_xyzw)
        self.limits,self.motor_enabled=limits,motor_enabled
        self.close_client,self.on_event=close_client,on_event
        self._lock=threading.Lock();self._stop=threading.Event();self._done=threading.Event()
        self._thread=None;self._version=0;self._reason=None
        self._state=dict(started=False,client_opened=False,finished=False,reason=None,error=None,stop_attempted=False,
                         stop_reply=None,stop_error=None,close_error=None,last_actual_reply=None,
                         latest_event=None,run_id=run_id,source=source,motor_enabled=motor_enabled,
                         authority='physical_display_follower_only',
                         transport_close_policy='root_callback' if close_client else 'frozen_client_cached_stop_rpc')

    def _set(self,**fields):
        with self._lock:self._state.update(fields)

    def snapshot(self):
        with self._lock:return copy.deepcopy(self._state)

    def _emit(self,event,**fields):
        record=dict(event=event,run_id=self.run_id,source=self.source,
                    observed_host_qpc_ns=str(time.perf_counter_ns()),**fields)
        self._set(latest_event=copy.deepcopy(record))
        if self.on_event is not None:self.on_event(copy.deepcopy(record))

    def _request_close(self,reason):
        with self._lock:
            if self._reason is None:self._reason=reason;self._state['reason']=reason
        self._stop.set()
        self.mailbox.close(reason)

    def start(self):
        with self._lock:
            if self._thread is not None or self._stop.is_set():raise RuntimeError('NO_FOLLOWER_RESTART')
            self._state['started']=True
            self._thread=threading.Thread(target=self._run,name='physical-follow-'+self.run_id[:40],daemon=False)
            self._thread.start()
        return self

    def close(self,reason='root_close',*,wait=False,timeout=None):
        """Default is nonblocking; wait=True is for Root's final cleanup path."""
        if type(reason) is not str or not reason:raise ValueError('EXPLICIT_CLOSE_REASON')
        if type(wait) is not bool:raise ValueError('EXPLICIT_WAIT_BOOL')
        self._request_close(reason)
        with self._lock:thread=self._thread
        if thread is None:
            self._set(finished=True);self._done.set();return True
        if wait:
            if threading.get_ident()==thread.ident:raise RuntimeError('IO_THREAD_CANNOT_JOIN_ITSELF')
            thread.join(timeout)
        return self._done.is_set()

    def _positive_guard(self):
        pending=self.mailbox.receive(self._version,timeout=0)
        packet=pending.get('packet')
        state=packet.get('native',{}) if type(packet) is dict else {}
        if pending['closed'] or self._stop.is_set():raise RuntimeError('FOLLOWER_CLOSED_NO_POSITIVE_IO')
        if state.get('fault') or state.get('phase')=='ARRIVED' or state.get('ready') is False:
            self._request_close('pending_terminal_native_source')
            raise RuntimeError('TERMINAL_PUBLICATION_NO_POSITIVE_IO')

    def _run(self):
        raw=follower=observed=None
        try:
            if self._stop.is_set():return
            mapper=self.api.FollowMapper(self.run_id,self.source,self.reference_xyzw,self.limits)
            raw=self.client_factory()
            if getattr(raw,'keepalive',None) is not False:raise ValueError('INDEPENDENT_KEEPALIVE_MUST_BE_DISABLED')
            adapter=self.api.SshClientAdapter(raw)
            observed=_ObservedClient(self,adapter)
            follower=self.api.Follower(observed,mapper,motor_enabled=self.motor_enabled,clock_ns=time.perf_counter_ns)
            self._set(client_opened=True)
            self._emit('client_factory_returned',client_opened=True,
                       physical_readiness='only_actual_client_replies_establish_status')
            wait_seconds=min(.01,self.limits.keepalive_period_ns/2_000_000_000)
            while not self._stop.is_set():
                received=self.mailbox.receive(self._version,timeout=wait_seconds)
                if received['closed']:
                    self._request_close(received['reason'] or 'mailbox_closed');break
                packet=received['packet']
                if packet is not None:
                    self._version=received['version']
                    target=follower.push(packet)
                    self._emit('derived_target',target=dataclasses.asdict(target))
                    if target.terminal:
                        self._request_close('source_terminal:'+target.terminal_reason);break
                if self._stop.is_set():break
                if follower.target is None:
                    # Root may initialize G05 only after client_opened. Until
                    # its first actual accepted source there is no command or
                    # lease to renew, and no useful startup elapsed-time cap.
                    continue
                follower.tick()
        except BaseException as error:
            self._set(error=type(error).__name__+': '+str(error))
            self._request_close('follower_error')
        finally:
            self._request_close(self._reason or 'worker_exit')
            if follower is not None:
                try:
                    if not follower.stopped:follower.stop(self._reason)
                except BaseException as error:
                    self._set(stop_error=type(error).__name__+': '+str(error))
                self._set(stop_reply=copy.deepcopy(follower.stop_reply),
                          stop_error=follower.stop_error,
                          stop_attempted=bool(observed and observed.stop_attempted))
            if raw is not None:
                try:
                    if self.close_client is None:raw.close()
                    else:self.close_client(raw,stop_already_attempted=bool(observed and observed.stop_attempted))
                except BaseException as error:self._set(close_error=type(error).__name__+': '+str(error))
            self._set(finished=True);self._done.set()
