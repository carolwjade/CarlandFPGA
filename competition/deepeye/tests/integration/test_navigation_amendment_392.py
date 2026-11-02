"""SYNTHETIC_TEST offline saved-ledger/parser and original-ref attachment gates."""
import json
import importlib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

from competition.deepeye.simulation.authority import navigation_session_profile as nav
from competition.deepeye.simulation.authority import g05_csr_channels_v1 as channels
from competition.deepeye.simulation.authority.source_projection_v1 import assembler

E=Path(r'C:/Users/CarlJade/Documents/ChatGPT/FPGA多机协作开发/.planning/deepeye-resume-20261018/gen4-functional-chain-offboard-20261030-07/demo30h-navigation-180s-392/amendment-01')
IDENT=(1,0,0,0,0,0,0,0,2,0,0,0,7)


class NavigationAmendmentControls(unittest.TestCase):
    def test_fixed_navigation_source_pin_commitment_matches_four_actual_modules(self):
        selected=nav.NAV_ADJACENT_180S
        for name,_pin in selected.source_pins:importlib.import_module(assembler._PREFIX+name)
        source=NS(_navigation_profile=selected);book=NS(_source=source,_navigation_profile=selected)
        source._source_book=book
        modules=assembler._checked_original_modules(book)
        self.assertEqual(set(modules),{'root_source_book','_world_loop','_actor_source_custody','original_world_actor_link'})
        self.assertEqual(selected.profile_id,'DEEPEYE-NAV-ADJACENT-180S-V2')
        self.assertEqual(dict(selected.source_pins)['root_source_book'],
            'c83f35ad9b6985f8949e899b195898832b88cbd4ff8a314979c08a412b271e4e')
        self.assertEqual(dict(selected.source_pins)['_world_loop'],
            'ac9d07ea8941665d8cb1bfb83425941d98215a53bfcfed78c3d6836fc092a763')

    def test_wrong_source_pair_and_default_selector_on_new_sources_are_rejected(self):
        selected=nav.NAV_ADJACENT_180S
        for name,_pin in selected.source_pins:importlib.import_module(assembler._PREFIX+name)
        bad=tuple((name,'0'*64 if name=='root_source_book' else pin) for name,pin in selected.source_pins)
        with self.assertRaises(ValueError):replace(selected,source_pins=bad)
        with self.assertRaises(assembler.Rejected):assembler._checked_original_modules(NS(_navigation_profile=None))
        source=NS(_navigation_profile=None);book=NS(_source=source,_navigation_profile=selected);source._source_book=book
        with self.assertRaises(assembler.Rejected):assembler._checked_original_modules(book)

    def test_health_selector_requires_original_source_book_chain_and_owned_identity(self):
        selected=nav.NAV_ADJACENT_180S
        source=NS(_navigation_profile=selected);book=NS(_source=source,_navigation_profile=selected)
        source._source_book=book
        original=NS(refs=NS(chain=NS(sequence=NS(demo_cycle_profile=selected)),book=book,
            source=NS(source=source,book=book)),config=NS(owned_invocation_v1=NS(navigation_profile=selected)))
        self.assertIs(channels.G05CsrChannels._cycle_profile(original),selected)
        source._navigation_profile=None
        with self.assertRaises(ValueError):channels.G05CsrChannels._cycle_profile(original)
        source._navigation_profile=selected;original.refs.chain.sequence.demo_cycle_profile={'profile_id':selected.profile_id,'sha256':selected.sha256}
        with self.assertRaises((TypeError,ValueError)):channels.G05CsrChannels._cycle_profile(original)

    def test_saved_original_synthetic_init_and_large_status_need_explicit_navigation(self):
        initial=json.loads((E/'saved-facts/init.json').read_bytes())
        status=json.loads((E/'saved-facts/status.json').read_bytes())
        for value in (initial,status):
            try:
                result=channels.validate_csr_facts(value,identity_words=IDENT,
                    operation_id='SYNTHETIC_TEST_A392',demo_cycle_profile=nav.NAV_ADJACENT_180S)
            except (TypeError,ValueError) as error:self.fail('trusted navigation profile is not forwarded: '+str(error))
            self.assertEqual(result['deadline_board_ns'][1]-result['deadline_board_ns'][0],180_000_000_000)
            with self.assertRaises(ValueError):channels.validate_csr_facts(value,identity_words=IDENT,
                operation_id='SYNTHETIC_TEST_A392')
        self.assertGreater(len(status['receipts']),450)
        result=channels.validate_csr_facts(status,identity_words=IDENT,operation_id='SYNTHETIC_TEST_A392',
            previous=initial['receipts'],demo_cycle_profile=nav.NAV_ADJACENT_180S)
        self.assertEqual(len(result['receipts']),1751)

    def test_original_action_references_above32_are_retained_only_for_same_typed_navigation(self):
        def producer(selected):
            source=NS(_navigation_profile=selected);owner=NS();book=NS(_owner=owner,_navigation_profile=selected)
            link=NS(owner=owner,book=book,source=source,_registered=lambda:None)
            source._source_book=book;book._source=source
            book._actor_custody=NS(link=link,book=book,transitions=[],_context=lambda:None)
            return assembler.Producer(assembler._KEY,owner,link,book,{}),book
        for selected,count in ((None,32),(nav.NAV_ADJACENT_180S,33)):
            p,book=producer(selected);refs=[object() for _ in range(33)]
            book._actor_custody.transitions.extend(refs)
            for reference in refs[:32]:p.attach_transition(reference,successor_root=None,fields={})
            if selected is None:
                with self.assertRaises(assembler.Rejected):p.attach_transition(refs[32],successor_root=None,fields={})
            else:
                try:p.attach_transition(refs[32],successor_root=None,fields={})
                except assembler.Rejected as error:self.fail('33rd original navigation reference rejected: '+str(error))
            self.assertEqual(len(p._actions),count)
            self.assertTrue(all(entry[0] is reference for entry,reference in zip(p._actions,refs)))
            self.assertEqual(len(book._actor_custody.transitions),33)
        p,book=producer(nav.NAV_ADJACENT_180S)
        reference=object();book._actor_custody.transitions.append(reference)
        book._source._navigation_profile=None
        with self.assertRaises((assembler.Rejected,ValueError)):p.attach_transition(reference,successor_root=None,fields={})
        self.assertEqual(p._actions,[])


if __name__=='__main__':unittest.main()
