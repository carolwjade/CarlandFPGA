"""Synthetic raw CSR/wire controls; no board, event or motion authority."""
import copy
import json
import unittest

from competition.deepeye.tests.integration.test_g05_csr_channels_v1 import fixture, IDENTITY, OP
from competition.deepeye.simulation.authority import g05_csr_channels_v1 as channel
from competition.deepeye.simulation.authority.navigation_session_profile import NAV_ADJACENT_180S
from competition.deepeye.tools.diagnostic import functional50_chain_v2_board_a as board
from competition.deepeye.tools.diagnostic import functional50_g05_session_a as session
from competition.deepeye.tools.diagnostic import functional50_g05_transaction_a as transaction


def held_fixture():
    value=fixture();previous=copy.deepcopy(value['receipts']);rows=value['receipts']
    def read(offset,result):
        i=len(rows)+1
        a=dict(request_id='synthetic-held-v2',io=i,kind='read',offset=offset,value=None,pid=1,monotonic_ns=i*10)
        z=dict(request_id=a['request_id'],io=i,kind='read',value=result,monotonic_ns=i*10+1)
        rows.append(dict(index=i,started_raw_hex=channel._raw(a).hex(),returned_raw_hex=channel._raw(z).hex()))
    first=len(rows)+1
    for i,v in enumerate(IDENTITY):read(0x100+4*i,v)
    words=[65539]+[0]*29+[IDENTITY[12],0x47303550]
    read(0x1c,65540);read(0x300,65539)
    for i,w in enumerate(words):read(0x300+4*i,w)
    read(0x300,65539);read(0x1c,65541)
    capture=dict(status_before_latch=0x11,fault_before_latch=0,words32=words,
        status_before_snapshot=0x31,status_after_snapshot=0x31,result_seq=65539,
        tick_unit='50MHz_cycles',capture_kind='g05_held_bank_v2',held_before_seq=65539,
        held_after_seq=65539,latest_before_seq=65540,latest_after_seq=65541)
    value.update(kind='apply',phase_io_first=first,phase_io_last=len(rows),capture=capture,
                 deadline_board_monotonic_ns=10000)
    return value,previous


class HeldWireControls(unittest.TestCase):
    def test_navigation_capacity_includes_two_actual_held_reads_per_command(self):
        from competition.deepeye.tools.diagnostic import functional50_demo_four_cycle_profile_a as demo
        args=dict(max_commands=16,max_polls=128,duration_ns=180_000_000_000)
        self.assertEqual(demo.validate_caps(NAV_ADJACENT_180S,max_io=2048,**args),1786)
        with self.assertRaises(ValueError):demo.validate_caps(NAV_ADJACENT_180S,max_io=1785,**args)

    def test_raw_held_and_advancing_latest_round_trip(self):
        value,previous=held_fixture();cap=value['capture']
        obj=session.HeldCaptureFactsV2(cap['status_before_latch'],cap['fault_before_latch'],tuple(cap['words32']),
            cap['status_before_snapshot'],cap['status_after_snapshot'],cap['result_seq'],cap['held_before_seq'],
            cap['held_after_seq'],cap['latest_before_seq'],cap['latest_after_seq'])
        receipts=tuple(transaction.IOReceipt(x['index'],bytes.fromhex(x['started_raw_hex']),
            bytes.fromhex(x['returned_raw_hex'])) for x in value['receipts'])
        facts=session.SessionFacts(value['schema'],'apply',OP,value['policy_sha256'],0,10000,
            value['phase_io_first'],value['phase_io_last'],IDENTITY,1,0,obj,receipts,(),'ACTIVE')
        encoded=board.facts_json(facts,session,transaction,NAV_ADJACENT_180S)
        self.assertEqual(encoded,value)
        parsed=channel.validate_csr_facts(encoded,identity_words=IDENTITY,operation_id=OP,
            previous=previous,demo_cycle_profile=NAV_ADJACENT_180S)
        self.assertEqual(parsed['kind'],'apply')
        self.assertNotIn('motion_authority',parsed)

    def test_held_metadata_cannot_replace_actual_reads_or_legacy_gate(self):
        value,previous=held_fixture()
        with self.assertRaises(ValueError):
            channel.validate_csr_facts(value,identity_words=IDENTITY,operation_id=OP,previous=previous)
        for key,new in (('held_after_seq',65538),('latest_after_seq',65539),('result_seq',65540)):
            altered=copy.deepcopy(value);altered['capture'][key]=new
            with self.assertRaises(ValueError):
                channel.validate_csr_facts(altered,identity_words=IDENTITY,operation_id=OP,
                    previous=previous,demo_cycle_profile=NAV_ADJACENT_180S)
        altered=copy.deepcopy(value);row=altered['receipts'][-2]
        raw=json.loads(bytes.fromhex(row['returned_raw_hex']));raw['value']=65540
        row['returned_raw_hex']=channel._raw(raw).hex()
        with self.assertRaises(ValueError):
            channel.validate_csr_facts(altered,identity_words=IDENTITY,operation_id=OP,
                previous=previous,demo_cycle_profile=NAV_ADJACENT_180S)


if __name__=='__main__':unittest.main()
