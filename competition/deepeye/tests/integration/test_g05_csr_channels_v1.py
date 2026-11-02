"""NEW pure parser/configuration controls, never production/board authority.

All CSR bytes in this file are explicitly synthetic examples. A successful
parse does not create a live session, original event, BOOT, AI or movement.
Root executes this new group under its bounded runner; no native process here.
"""
import copy
import json
import unittest

from competition.deepeye.simulation.authority import g05_csr_channels_v1 as g
from competition.deepeye.simulation.authority.actor_composition import (
    _production_channels, ActivationUnavailable)
from competition.deepeye.simulation.authority.owned_invocation_v1.adapter import OwnedInvocationPolicy


IDENTITY=tuple(range(1,14))
OP='SYNTHETIC_PARSER_ONLY'


def fixture():
    rows=[]
    def io(kind,offset,value):
        i=len(rows)+1
        start=dict(request_id='synthetic',io=i,kind=kind,offset=offset,
                   value=None if kind=='read' else value,pid=1,monotonic_ns=i*10)
        end=dict(request_id='synthetic',io=i,kind=kind,
                 value=value if kind=='read' else None,monotonic_ns=i*10+1)
        rows.append(dict(index=i,started_raw_hex=g._raw(start).hex(),returned_raw_hex=g._raw(end).hex()))
    for offset,value in [(0,0x47303550),(4,2),(8,0),(16,0)]:io('read',offset,value)
    first=len(rows)+1
    for i,v in enumerate(IDENTITY):io('write',0x100+4*i,v)
    io('write',12,1)
    for i,v in enumerate(IDENTITY):io('read',0x100+4*i,v)
    io('read',8,1);io('read',16,0)
    return dict(schema='g05_csr_session_v2',kind='init',operation_id=OP,policy_sha256='1'*64,
        deadline_selected_lower_board_monotonic_ns=0,deadline_board_monotonic_ns=1000,
        phase_io_first=first,phase_io_last=len(rows),identity_words=list(IDENTITY),status=1,
        fault=0,capture=None,receipts=rows,unresolved_receipts=[],state='ACTIVE',authority='not_evaluated')


def mutate_raw(facts,index,key,value,part='returned_raw_hex'):
    row=facts['receipts'][index]
    obj=json.loads(bytes.fromhex(row[part]));obj[key]=value;row[part]=g._raw(obj).hex()


class CsrFactsControls(unittest.TestCase):
    def test_synthetic_full13_parser_result_never_authority(self):
        result=g.validate_csr_facts(fixture(),identity_words=IDENTITY,operation_id=OP)
        self.assertEqual(result['kind'],'init')
        self.assertNotIn('boot',result);self.assertNotIn('movement_authorized',result)

    def test_full_identity_readback_not_just_header_is_required(self):
        facts=fixture();mutate_raw(facts,20,'value',999)
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP)

    def test_unresolved_original_io_cannot_become_health(self):
        facts=fixture();facts['unresolved_receipts']=[{}]
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP)

    def test_reversed_original_call_bracket_is_refused(self):
        facts=fixture();mutate_raw(facts,10,'monotonic_ns',0)
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP)

    def test_wrong_same_load_magic_is_refused(self):
        facts=fixture();mutate_raw(facts,0,'value',0xdeadbeef)
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP)

    def test_changed_cumulative_prefix_is_refused(self):
        facts=fixture();prefix=copy.deepcopy(facts['receipts'][:4]);prefix[0]['returned_raw_hex']='00'
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP,previous=prefix)

    def test_explicit_fault_cannot_become_bound_health(self):
        facts=fixture();facts['fault']=1
        with self.assertRaises(ValueError):g.validate_csr_facts(facts,identity_words=IDENTITY,operation_id=OP)


class OptInControls(unittest.TestCase):
    def test_default_factory_stays_unavailable_before_acquisition(self):
        with self.assertRaises(ActivationUnavailable):_production_channels(object())

    def test_json_or_foreign_binding_cannot_select_production(self):
        with self.assertRaises(ValueError):g.select_original_g05({}, {})

    def test_demo_age_is_bounded_and_strict(self):
        for value in (True,0,5_000_000_001):
            with self.assertRaises(ValueError):g.G05CsrPolicy(value,1,0,0).check()

    def test_original_command_duration_remains100ms(self):
        args=('synthetic','1'*64,'2'*40,2,2,2)
        with self.assertRaises(ValueError):OwnedInvocationPolicy(*args,1000).check()
        OwnedInvocationPolicy(*args,1000,demo_duration_v1=True).check()
        with self.assertRaises(ValueError):OwnedInvocationPolicy(*args,1001,demo_duration_v1=True).check()


if __name__=='__main__':unittest.main()
