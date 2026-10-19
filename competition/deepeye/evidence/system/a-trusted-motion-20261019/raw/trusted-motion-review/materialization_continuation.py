"""Observe continuation after the same materialization fault; no new source mutation."""
import json
from unittest.mock import patch
from competition.deepeye.tests.simulation import test_motion_executor as t

f=t.MotionExecutorTests();f.setUp();ex=f.make()
first=ex.commit_step(f.prepare(ex),lambda:f.fence())
try:
    with patch.object(t.m.p,'materialize_committed_transition',side_effect=MemoryError('authority audit allocation unavailable')):
        ex.passage_state()
except MemoryError:
    observed=True
else:
    observed=False
after_failure={'stopped':ex.controller_view().stopped,'trial_failed':ex.controller_view().trial_failed,'pose_revision':ex.renderer_view().pose_revision}
second=ex.commit_step(f.prepare(ex),lambda:f.fence(start=1_020_000_000))
print(json.dumps({'materialization_error_observed':observed,'after_failure':after_failure,
                  'second_commit_without_boot_or_readmission':{'pose_revision':second.pose_revision,'start_ns':second.start_ns,'end_ns':second.end_ns},
                  'same_boot':first.boot is second.boot,'same_command':first.command_seq==second.command_seq,
                  'all_records_are_explicit_software_fixtures':True},sort_keys=True))
