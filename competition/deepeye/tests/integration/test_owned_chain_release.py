"""New invocation controls; these never acquire an engine or board."""
import importlib
import unittest


class OwnedChainReleaseTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module(
            'competition.deepeye.tools.run_owned_chain_headless')
        self.plan = dict(schema=1, task_id='DEEPEYE-IMPLEMENTATION-20261014',
            task_version=1, work_id=self.module.WORK,
            mode='WORLD_INITIAL_VIEW_SOURCE_ONLY',
            requirements_sha256=self.module.REQUIREMENTS)
        self.release = dict(schema=1, work_id=self.module.WORK, allowed=True,
            plan_sha256='a'*64, ordinal=1, maximum_engine_creates=1,
            mode='WORLD_INITIAL_VIEW_SOURCE_ONLY')

    def test_movement_scope_refused_before_any_owner(self):
        self.plan['mode'] = 'MOTION'
        with self.assertRaises(ValueError):
            self.module._release_guard(self.plan, self.release, 'a'*64)

    def test_changed_plan_or_multiple_engine_release_refused(self):
        with self.assertRaises(ValueError):
            self.module._release_guard(self.plan, self.release, 'b'*64)
        self.release['maximum_engine_creates'] = 2
        with self.assertRaises(ValueError):
            self.module._release_guard(self.plan, self.release, 'a'*64)

    def test_contract_change_refused_before_any_owner(self):
        self.plan['requirements_sha256'] = 'b'*64
        with self.assertRaises(ValueError):
            self.module._release_guard(self.plan, self.release, 'a'*64)

    def test_failed_clock_cannot_prevent_original_cleanup(self):
        class Original:
            calls = 0

            def close(self, reason):
                self.calls += 1
                return dict(slots=dict(process=dict(state='NOT_ACQUIRED'),
                    job=dict(state='NOT_ACQUIRED')), wait_result=None,
                    exit_code=None, job_active_processes=None)

        def failed_clock():
            raise ValueError('original QPC permanently failed')

        original = Original()
        history = self.module._close(original, failed_clock)
        self.assertEqual(original.calls, 1)
        self.assertEqual(len(history), 1)


if __name__ == '__main__':
    unittest.main()
