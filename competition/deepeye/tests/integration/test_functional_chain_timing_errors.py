"""NEW timing error fixtures only; original seven test methods are never invoked."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location('functional_timing_fixture_utilities',
                                             HERE / 'test_functional_chain_timing.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
C, H = F.C, F.H


class Transport:
    def __init__(self, owner, clock, mode='valid'):
        self.owner, self.clock, self.mode = owner, clock, mode
        self.raw = None
        self.responses = 0
    def send_once(self, raw): self.raw = raw
    def line(self, seconds):
        if self.raw is None: return F.ready()
        self.responses += 1
        if self.mode == 'clock_second' and self.responses == 2:
            def unavailable(): raise OSError('fixture current QPC unavailable')
            self.owner._clock = unavailable
            return b'{}\n'
        q = json.loads(self.raw)
        self.clock.value = q['original_host_qpc_ns'][0] + (2000000001 if self.mode == 'stale' else 150000000)
        obj = F.capture(self.raw)
        if self.mode == 'identity': obj['context']['session_id'] = 'wrong'
        if self.mode == 'ack': obj['captures'][0]['ack_returned'] = False
        return C.encode(obj)
    def close_input(self): pass


def owner():
    clock = F.Clock()
    owned = C._HostOwner(F.CTX, clock, max_age_ns=2000000000, functional_timing_profile=dict(F.PROFILE))
    owned.host_clock = types.SimpleNamespace(metadata={'fixture_only': True})
    return owned, clock


def reject_timing_save(real_save):
    def save(path, value):
        if path.name.startswith('response-timing-'): raise OSError('fixture timing sink unavailable')
        return real_save(path, value)
    return save


class TimingErrorTests(unittest.TestCase):
    def exchange_error(self, mode):
        owned, clock = owner()
        with tempfile.TemporaryDirectory() as tmp, patch.object(H, 'save', reject_timing_save(H.save)):
            try: H._exchange(owned, Transport(owned, clock, mode), C, [17,4095,32769,65280], [2,17,128,254], 1, Path(tmp))
            except BaseException as error: return error
        self.fail('fixture must fail, never swallow a timing save error')

    def test_original_stale_identity_ack_error_survives_timing_save_failure(self):
        for mode, message in [('stale','diagnostic response expired; arrival cannot renew source'),
                              ('identity','original pending request correlation mismatch'),
                              ('ack','raw diagnostic lane mismatch')]:
            with self.subTest(mode=mode):
                error = self.exchange_error(mode)
                self.assertIs(type(error), ValueError)
                self.assertEqual(str(error), message)
                self.assertEqual(getattr(error, '_private_timing_save_errors', None),
                    ({'stage':'response_timing_save', 'type':'OSError', 'message':'fixture timing sink unavailable'},))

    def test_accepted_capture_still_fails_when_timing_save_fails(self):
        error = self.exchange_error('valid')
        self.assertIs(type(error), OSError)
        self.assertEqual(str(error), 'fixture timing sink unavailable')

    def test_second_qpc_failure_cannot_reuse_first_accepted_timing(self):
        owned, clock = owner()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with self.assertRaisesRegex(OSError, 'fixture current QPC unavailable'):
                H._exchange(owned, Transport(owned, clock, 'clock_second'), C,
                            [17,4095,32769,65280], [2,17,128,254], 2, out)
            self.assertIsNone(owned.last_response_timing)
            self.assertEqual([p.name for p in out.glob('response-timing-*.json')], ['response-timing-00.json'])

    def test_main_terminal_keeps_primary_and_secondary_without_acquisition(self):
        original = self.exchange_error('stale')
        sys.path.insert(0, str(ROOT))
        from competition.deepeye.integration import host_clock
        clock = F.Clock(); clock.metadata = {'domain_id':'d'*32}
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); template = base/'template.json'; out = base/'new-host'
            context = {k:v for k,v in F.CTX.items() if k not in ('request_hash','clock_domain_id')}
            template.write_text(json.dumps({'context':context,'agent_source_commit':'b'*40}), encoding='utf-8')
            argv = ['--template',str(template),'--template-sha256',H.pin(template)['sha256'],'--out',str(out)]
            with patch.object(host_clock,'qpc_clock_for_new_run',return_value=clock), \
                 patch.object(H,'_original_process_identity',return_value={'fixture_only':True}), \
                 patch.object(H,'_wait_activation',return_value=None), \
                 patch.object(H,'_claim',side_effect=original):
                self.assertEqual(H.main(argv), 2)
            terminal = json.loads((out/'HOST_TERMINAL.json').read_bytes())
        self.assertEqual(terminal['primary_error'], {'type':'ValueError',
                         'message':'diagnostic response expired; arrival cannot renew source'})
        self.assertEqual(terminal['secondary_errors'], [{'stage':'response_timing_save','type':'OSError',
                                                       'message':'fixture timing sink unavailable'}])
        self.assertIs(terminal['SSH_started'], False)


if __name__ == '__main__': unittest.main(verbosity=2)
