"""A independent offline persistence/rollback probes; no App transport allowed.

Usage: python independent_probe.py SOURCE_ROOT [--v1]
All SQLite and declaration mutations occur in disposable fixtures below SOURCE_ROOT/.local.
"""
import asyncio
import json
import pathlib
import sqlite3
import sys
import tempfile
from dataclasses import replace

source = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source))
from fpga_mesh.sessions import MainSessionRouter, ExternalDeliveryPending
from fpga_mesh.store import SQLiteStore
from fpga_mesh.gateway import AppServerGateway, GatewayConfig
from fpga_mesh.controller import Controller
from fpga_mesh.update import assert_idle, stop_idle_node
from tests.test_sessions import event

requests = []
def forbidden_client():
    requests.append('unexpected client request')
    raise AssertionError('No App client may be opened by these probes')

class Fixture:
    def __init__(self):
        (source/'.local').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=source/'.local', prefix='a-offline-probe-')
        self.root = pathlib.Path(self.temp.name)
        self.router = MainSessionRouter(self.root/'main_sessions.sqlite')
        self.store = SQLiteStore(self.root/'state.sqlite')
        with self.router.db:
            self.router.db.execute('INSERT INTO main_sessions VALUES (?,?,?,?,?,?,?,?,?)',
                ('a-fixture-task', 'a-fixture-director', 1, 'gpt-6-astra', 'medium',
                 'execution', 'fixture', None, '2026-10-16T00:00:00+00:00'))
        self.gateway = AppServerGateway(GatewayConfig(node_id='B',role='astra',model='gpt-6-astra',
            provider='openai',reasoning_effort='medium',cwd=str(self.root),codex_home=str(self.root)),
            client_factory=forbidden_client,session_router=self.router)
        self.controller = Controller(self.store,self.gateway)
        self.config = self.root/'node.toml'
        self.config.write_text('node_id="B"\nstate_dir="."\n',encoding='utf-8')
    def declare(self):
        self.router.external_owners_path.write_text(json.dumps({'a-fixture-task':{
            'owner_kind':'desktop','thread_id':'a-fixture-director','task_version':1}}),encoding='utf-8')
    async def defer(self,label,version=1):
        m=replace(event('a-fixture-task',label),task_version=version)
        await self.controller.offer(m)
        await self.controller.run_until_idle()
        return m,self.router.external_delivery(m.message_id)
    def args(self,m,d,action='withdraw'):
        return dict(operation_id='a-fixture-op:'+m.message_id,action=action,message_id=m.message_id,
            task_id=m.task_id,task_version=m.task_version,recipient_thread_id=d['recipient_thread_id'],
            reviewer_thread_id='a-fixture-director',evidence='offline fixture established zero App requests',
            reason='explicitly reconcile invalid declaration fixture',followup_work_id='a-fixture-followup',
            confirmed_not_sent=True)
    async def reopen(self):
        await self.gateway.close()
        self.router.close(); self.store.close()
        self.router=MainSessionRouter(self.root/'main_sessions.sqlite')
        self.store=SQLiteStore(self.root/'state.sqlite')
        self.gateway.session_router=self.router
        self.controller=Controller(self.store,self.gateway)
    async def close(self):
        await self.gateway.close()
        self.router.close();self.store.close();self.temp.cleanup()

def rejected(call):
    try: call()
    except (ValueError,sqlite3.IntegrityError) as exc: return str(exc)
    raise AssertionError('operation unexpectedly succeeded')

async def bad_declaration(mode,v1):
    f=Fixture()
    try:
        if mode=='malformed':f.router.external_owners_path.write_text('{',encoding='utf-8')
        else:f.declare()
        m,d=await f.defer(mode,2 if mode=='wrong_version' else 1)
        f.declare()
        receipt=dict(message_id=m.message_id,task_id=m.task_id,task_version=m.task_version,
            thread_id='a-fixture-director',turn_id='fixture-no-turn',evidence='offline-negative-probe')
        error=rejected(lambda:f.router.external_receipt(**receipt))
        f.router.external_owners_path.unlink()
        rejected(lambda:assert_idle(f.config,node='B'))
        if v1:
            assert not hasattr(f.router,'external_transition')
            return {'case':mode,'original_dead_end_reproduced':True,'receipt_error':error}
        args=f.args(m,d)
        closed=f.router.external_transition(**args)
        assert not closed['execute'] and closed['delivery']['status']=='withdrawn_unconsumed'
        assert closed['delivery']['envelope']==d['envelope']
        assert closed['delivery']['declaration_hash']==d['declaration_hash']
        await f.reopen()
        assert f.router.external_transition(**args)==closed
        assert f.store.pending_inbound()==[]
        rejected(lambda:f.router.external_receipt(**receipt))
        rejected(lambda:f.router.external_transition(**{**args,'reason':'changed payload'}))
        await f.gateway.handle(m)
        called=[]
        stop_idle_node(f.config,node='B',stop=lambda:called.append('fixture callback only'))
        assert called==['fixture callback only']
        return {'case':mode,'closed_without_consumption':True,'both_ledgers_reopened':True,
            'original_identity_preserved':True,'idempotent':True,'replay_prevented':True}
    finally:await f.close()

async def unknown_restart():
    f=Fixture()
    try:
        f.declare();m,d=await f.defer('unknown')
        args=f.args(m,d,'attempt')
        assert f.router.external_transition(**args)['execute']
        await f.reopen()
        assert not f.router.external_transition(**args)['execute']
        rejected(lambda:f.router.external_transition(**{**args,'operation_id':'withdraw-after-reopen','action':'withdraw'}))
        f.router.external_owners_path.unlink()
        called=[]
        rejected(lambda:assert_idle(f.config,node='B'))
        rejected(lambda:stop_idle_node(f.config,node='B',stop=lambda:called.append(True)))
        assert not called and f.router.result(m.message_id)['status']=='delivery_unknown'
        try:await f.gateway.handle(m)
        except ExternalDeliveryPending:pass
        else:raise AssertionError('unknown replay not held')
        return {'case':'unknown_restart','execute_once':True,'withdraw_rejected':True,
            'both_ledgers_reopened':True,'idle_and_stop_rejected_without_owner_file':True}
    finally:await f.close()

async def supersession_restart():
    f=Fixture()
    try:
        f.declare();old,d=await f.defer('original')
        new,n=await f.defer('explicit successor',2)
        args=f.args(old,d,'supersede');args['successor_message_id']=new.message_id
        saved=f.router.external_transition(**args)
        await f.reopen()
        assert f.router.external_transition(**args)==saved
        assert f.router.external_delivery(new.message_id)==n
        f.router.external_owners_path.unlink()
        rejected(lambda:assert_idle(f.config,node='B'))
        await f.gateway.handle(old)
        return {'case':'supersession_restart','original_closed':True,'successor_preserved_pending':True,
            'both_ledgers_reopened':True,'idle_blocked_by_successor':True}
    finally:await f.close()

async def atomic_rollback():
    f=Fixture()
    try:
        f.declare();m,d=await f.defer('rollback')
        args=f.args(m,d,'attempt')
        with f.router.db:
            f.router.db.execute("CREATE TRIGGER reject_transition BEFORE UPDATE ON main_runs BEGIN SELECT RAISE(ABORT,'injected fixture failure'); END")
        rejected(lambda:f.router.external_transition(**args))
        assert f.router.external_delivery(m.message_id)==d
        assert f.router.db.execute('SELECT count(*) FROM external_actions').fetchone()[0]==0
        assert f.router.result(m.message_id)['status']=='delivery_pending'
        with f.router.db:f.router.db.execute('DROP TRIGGER reject_transition')
        assert f.router.external_transition(**args)['execute']
        await f.reopen()
        assert not f.router.external_transition(**args)['execute']
        return {'case':'atomic_rollback','all_three_writes_rolled_back':True,'same_operation_can_retry_only_after_rollback':True,
            'committed_attempt_cannot_replay':True}
    finally:await f.close()

async def main():
    old='--v1' in sys.argv
    results=[await bad_declaration(mode,old) for mode in ['malformed','wrong_version']]
    if not old:results += [await unknown_restart(),await supersession_restart(),await atomic_rollback()]
    assert not requests
    print(json.dumps({'source_mode':'original_v1' if old else 'candidate_v2','cases':results,
        'client_factory_calls':len(requests),'real_app_requests':0,'offline_only':True},indent=2))
asyncio.run(main())
