"""Behavior tests for the launcher's fail-closed preparation and verdict."""
import os
from pathlib import Path
import tempfile
import unittest

from simulation.isolation.policy import create_run_directory, minimal_environment, evaluate, parse_fixture
import json
from copy import deepcopy


class PolicyTests(unittest.TestCase):
    def test_refuses_existing_run_without_touching_it(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            existing = Path(parent) / 'existing'
            existing.mkdir()
            marker = existing / 'owner.txt'
            marker.write_text('other owner')
            with self.assertRaises(FileExistsError):
                create_run_directory(Path(parent), 'existing')
            self.assertEqual(marker.read_text(), 'other owner')

    def test_rejects_escape_and_reserved_names(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            for name in ('..', '../escape', r'..\escape', 'C:\\escape', 'CON', '', 'a:b'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    create_run_directory(Path(parent), name)

    def test_environment_is_built_without_inheriting_credentials(self):
        env = minimal_environment(Path('C:/fixture/temp'), 'C:/Windows', 'C:/fixture/local')
        self.assertEqual(set(env), {'SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'LOCALAPPDATA'})
        self.assertEqual(env['LOCALAPPDATA'], 'C:/fixture/local')
        self.assertNotIn('PATH', env)
        self.assertNotIn('PYTHONPATH', env)

    def _evidence(self):
        return {
            'trusted': {'is_appcontainer': True, 'sid_matches': True,
                        'capability_count': 0, 'win32k_disabled': True,
                        'child_process_restricted': True, 'in_job': True,
                        'resumed_after_verification': True, 'job_limits_match': True},
            'fixture': {'model_ok': True, 'pipe_ok': True,
                        'truth_open_error': 5, 'canary_handle_error': 6,
                        'process_access_errors': {str(x): 5 for x in (8, 16, 32, 64, 128)}},
            'parent_controls': {'truth_exists': True, 'truth_read_ok': True,
                                'canary_handle_read_ok': True, 'model_hash_ok': True,
                                'process_access_ok': True},
            'inheritance': {'verified': True},
            'lifecycle': {'exit_code': 0, 'terminal': True,
                          'profile_deleted': True},
        }

    def test_verdict_requires_all_positive_controls(self):
        for group, key in [('fixture', 'model_ok'), ('fixture', 'pipe_ok'),
                           ('parent_controls', 'truth_exists'),
                           ('parent_controls', 'process_access_ok'),
                           ('trusted', 'win32k_disabled'),
                           ('lifecycle', 'profile_deleted')]:
            evidence = self._evidence()
            evidence[group][key] = False
            self.assertFalse(evaluate(evidence)['passed'], (group, key))

    def test_missing_canary_is_not_access_denied(self):
        evidence = self._evidence()
        evidence['fixture']['truth_open_error'] = 2
        self.assertFalse(evaluate(evidence)['passed'])

    def test_successful_dangerous_process_open_fails_verdict(self):
        evidence = self._evidence()
        evidence['fixture']['process_access_errors']['64'] = 0
        self.assertFalse(evaluate(evidence)['passed'])

    def test_missing_evidence_fails_closed_and_complete_evidence_passes(self):
        self.assertFalse(evaluate({})['passed'])
        self.assertTrue(evaluate(self._evidence())['passed'])

    def test_only_ordered_last_canary_attempt_can_explain_fatal_invalid_handle(self):
        evidence = self._evidence()
        before = dict(evidence['fixture'])
        before.pop('canary_handle_error')
        frames = [{'phase': 'positive_controls', 'result': {'model_ok': True, 'pipe_ok': True}},
                  {'phase': 'boundaries', 'result': before},
                  {'phase': 'excluded_handle_attempt', 'handle': 1234}]
        raw = b'\n'.join(json.dumps(f).encode() for f in frames)
        fixture = parse_fixture(raw, 0xc0000008, 1234)
        self.assertEqual(fixture['canary_handle_error'], 0xc0000008)
        self.assertTrue(fixture['fatal_handle_denial_attested'])
        for bad_raw, exit_code, handle in [(raw, 0, 1234), (raw, 0xc0000142, 1234),
                                           (raw, 0xc0000008, 555),
                                           (json.dumps(frames[-1]).encode(), 0xc0000008, 1234)]:
            with self.subTest(exit_code=exit_code, handle=handle), self.assertRaises(ValueError):
                parse_fixture(bad_raw, exit_code, handle)
        evidence['fixture'] = fixture
        evidence['lifecycle']['exit_code'] = 0xc0000008
        evidence['trusted']['mitigation_raw'] = {'strict_handle': 3}
        self.assertTrue(evaluate(evidence)['passed'])
        evidence['trusted']['mitigation_raw']['strict_handle'] = 0
        self.assertFalse(evaluate(evidence)['passed'])
        evidence['trusted']['mitigation_raw']['strict_handle'] = 3
        evidence['fixture']['fatal_handle_denial_attested'] = False
        self.assertFalse(evaluate(evidence)['passed'])

    def test_parser_rejects_unbounded_and_incomplete_protocol(self):
        for raw in (b'x' * 4097, b'{}', b'not-json', b''):
            with self.subTest(raw=raw[:10]), self.assertRaises(ValueError):
                parse_fixture(raw, 0, 1234)

    def test_complete_frame_cannot_replace_prior_failed_or_missing_evidence(self):
        final = self._evidence()['fixture']
        boundary = deepcopy({key: value for key, value in final.items() if key != 'canary_handle_error'})
        frames = [{'phase': 'positive_controls', 'result': {'model_ok': True, 'pipe_ok': True}},
                  {'phase': 'boundaries', 'result': boundary},
                  {'phase': 'excluded_handle_attempt', 'handle': 1234},
                  {'phase': 'complete', 'result': final}]
        raw = lambda value: b'\n'.join(json.dumps(frame).encode() for frame in value)
        self.assertEqual(parse_fixture(raw(frames), 0, 1234), final)
        for mutate in (
                lambda f: f[0]['result'].__setitem__('model_ok', False),
                lambda f: f[0].__setitem__('result', {}),
                lambda f: f[1]['result'].__setitem__('truth_open_error', 0),
                lambda f: f[1]['result']['process_access_errors'].__setitem__('64', 0),
                lambda f: f[1]['result'].__setitem__('model_ok', 1),
                lambda f: f[3].__setitem__('result', {})):
            changed = deepcopy(frames)
            mutate(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                parse_fixture(raw(changed), 0, 1234)

    def test_fixture_rejects_nonobjects_duplicates_and_nonfinite_values(self):
        for raw in (b'null', b'[]', b'1', b'{"phase":"positive_controls","phase":"complete"}',
                    b'{"phase":"positive_controls","result":{"model_ok":NaN}}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_fixture(raw, 0, 1234)

    def test_numeric_overflow_and_nested_list_type_changes_are_rejected(self):
        boundary = deepcopy(self._evidence()['fixture'])
        boundary.pop('canary_handle_error')
        frames = [{'phase': 'positive_controls', 'result': {'model_ok': True, 'pipe_ok': True}},
                  {'phase': 'boundaries', 'result': boundary},
                  {'phase': 'excluded_handle_attempt', 'handle': 1234},
                  {'phase': 'complete', 'result': self._evidence()['fixture']}]
        raw = lambda value: b'\n'.join(json.dumps(frame).encode() for frame in value)
        overflow = deepcopy(frames)
        for index in (0, 1, 3):
            overflow[index]['result']['extra'] = 'EXPONENT_OVERFLOW'
        with self.assertRaises(ValueError):
            parse_fixture(raw(overflow).replace(b'"EXPONENT_OVERFLOW"', b'1e999'), 0, 1234)
        frames[0]['result']['vector'] = [True]
        frames[1]['result']['vector'] = [1]
        frames[3]['result']['vector'] = [1]
        with self.assertRaises(ValueError):
            parse_fixture(raw(frames), 0, 1234)

    @unittest.skipUnless(os.name == 'nt', 'Win32 ACL helper')
    def test_acl_directory_must_be_empty_before_inheritable_acl(self):
        from simulation.isolation import win32
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            owned = Path(parent) / 'owned'
            owned.mkdir()
            outside = Path(parent) / 'sibling.txt'
            outside.write_text('task-owned outside logical root')
            alias = owned / 'alias.txt'
            os.link(outside, alias)
            with patch.object(win32, 'SetNamedSecurityInfoW', return_value=0) as native:
                with self.assertRaises(ValueError):
                    win32.set_new_object_acl(owned, owned, win32.user_sid())
                native.assert_not_called()
            self.assertEqual(outside.read_text(), 'task-owned outside logical root')

    @unittest.skipUnless(os.name == 'nt', 'Win32 ACL helper')
    def test_acl_helper_rejects_dotdot_escape_before_modifying_objects(self):
        from simulation.isolation.win32 import set_new_object_acl
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as parent:
            owned = Path(parent) / 'owned'
            unrelated = Path(parent) / 'unrelated'
            owned.mkdir()
            unrelated.mkdir()
            with self.assertRaises(ValueError):
                set_new_object_acl(owned / '..' / 'unrelated', owned, 'invalid-sid-never-used')


if __name__ == '__main__':
    unittest.main()
