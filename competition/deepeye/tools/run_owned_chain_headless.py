"""One Root-released actual frozen world, initial view and causal source only.

This entry owns the original QPC, native process, frozen epoch and numerical
executor on one thread. It neither opens a board/model nor issues a command.
Run through the existing bounded Job supervisor with a fresh plan and release.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import time

from ..integration import host_clock
from ..simulation.authority import _owned_godot as native
from ..simulation.authority import _world_loop as loop
from ..simulation.authority import _world_values as values
from ..simulation.authority.motion import gate_geometry as gates
from ..simulation.authority.motion import workspace_boundaries as workspace
from ..simulation.authority.world_initial_pose import initial_pose_for_layout
from ..simulation.sensors.owned_world_field import OwnedWorldField
from .diagnostic.causal_pl_exchange import CausalSourcePump

WORK = 'A-GEN4-OWNED-WORLD-SOURCE-20261029-05'
REQUIREMENTS = 'c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
ENGINE = 'ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424'
MODE = 'WORLD_INITIAL_VIEW_SOURCE_ONLY'
LIMITS = dict(nodes=4096, objects=30, surfaces=64, unique_vertices=1000000,
              indices=3000000, snapshot_bytes=134217728, chunks=3072, depth=32)


def _json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate invocation key')
            out[key] = value
        return out
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def _raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _save(path, value):
    with path.open('xb') as stream:
        stream.write(_raw(value))


def _inside(path, root):
    path = Path(path).resolve()
    path.relative_to(root.resolve())
    return path


def _file(root, name):
    relative = PurePosixPath(name)
    if (type(name) is not str or str(relative) != name or relative.is_absolute()
            or '..' in relative.parts or '\\' in name or ':' in name):
        raise ValueError('strict relative source path required')
    return _inside(root/name, root)


def _release_guard(plan, release, plan_sha):
    required = {'schema', 'work_id', 'allowed', 'plan_sha256', 'ordinal',
                'maximum_engine_creates', 'mode'}
    if (type(plan) is not dict or type(release) is not dict or set(release) != required
            or type(plan.get('schema')) is not int or plan['schema'] != 1
            or plan.get('task_id') != 'DEEPEYE-IMPLEMENTATION-20261014'
            or type(plan.get('task_version')) is not int or plan['task_version'] != 1
            or plan.get('work_id') != WORK or plan.get('mode') != MODE
            or plan.get('requirements_sha256') != REQUIREMENTS
            or type(release['schema']) is not int or release['schema'] != 1
            or release['work_id'] != WORK or release['allowed'] is not True
            or release['mode'] != MODE or release['plan_sha256'] != plan_sha
            or type(release['ordinal']) is not int or release['ordinal'] != 1
            or type(release['maximum_engine_creates']) is not int
            or release['maximum_engine_creates'] != 1):
        raise ValueError('one hash-bound Root initial-view/source release required')


def _policy(project, catalog, pins, bundle, run_id):
    required = {'schema', 'catalog', 'presentation_part_ids', 'document_path',
                'canonical_path', 'catalog_path', 'writer_paths', 'allowed_script_paths'}
    if type(catalog) is not dict or set(catalog) != required or catalog['schema'] != 1:
        raise ValueError('complete independently reviewed source catalog required')
    def digest(name):
        actual = _sha(_file(project, name).read_bytes())
        if pins.get(name) != actual:
            raise ValueError('current policy source differs')
        return actual
    writers = catalog['writer_paths']
    if type(writers) is not list or len(writers) != 11 or len(set(writers)) != 11:
        raise ValueError('original eleven-writer wire inventory required')
    material = b'DEY-WRITERS-1\n'
    for name in sorted(writers):
        material += name.encode('utf-8')+b'\0'+bytes.fromhex(digest(name))
    entries = []
    for entry in catalog['catalog']:
        if type(entry) is not dict or set(entry) != {'kind', 'part_ids'}:
            raise ValueError('exact catalog part inventory required')
        entries.append(values.CatalogEntry(entry['kind'], tuple(entry['part_ids'])))
    return values.ValuePolicy(digest(catalog['document_path']), digest(catalog['canonical_path']),
        digest(catalog['catalog_path']), _sha(material), bundle, tuple(entries),
        tuple(catalog['presentation_part_ids']),
        tuple(digest(name) for name in catalog['allowed_script_paths']), run_id=run_id)


def _approved(plan_path, release_path):
    plan_raw, release_raw = plan_path.read_bytes(), release_path.read_bytes()
    plan, release = _json(plan_raw), _json(release_raw)
    _release_guard(plan, release, _sha(plan_raw))
    required = {'schema', 'task_id', 'task_version', 'work_id', 'mode',
        'requirements_sha256', 'operation_id', 'run_id', 'root_path', 'artifact_root',
        'worktree_path', 'python_files', 'dependency_path', 'dependency_files',
        'engine_path', 'project_path', 'project_files', 'source_bundle_sha256',
        'raw_layout_sha256', 'stdout_path', 'stderr_path', 'environment',
        'source_catalog_path', 'source_catalog_sha256', 'output_path',
        'initial_standoff_m', 'field_policy', 'sample_records'}
    if set(plan) != required:
        raise ValueError('exact source-only invocation plan required')
    root = Path(plan['root_path']).resolve()
    unit = _inside(plan['artifact_root'], root/'.planning/deepeye-resume-20261018')
    _inside(plan_path, unit); _inside(release_path, unit)
    contract = _json((root/'docs/competition/deepeye-2026/immutable_scope.json').read_bytes())
    if _sha(_raw(contract['requirements'])) != REQUIREMENTS:
        raise ValueError('human H01-H15 requirements changed')
    worktree = Path(plan['worktree_path']).resolve()
    if Path(__file__).resolve() != worktree/'competition/deepeye/tools/run_owned_chain_headless.py':
        raise ValueError('runner is not original approved current source')
    for area, records in ((worktree, plan['python_files']),
                          (Path(plan['dependency_path']).resolve(), plan['dependency_files'])):
        if type(records) is not list or not records or len(dict(records)) != len(records):
            raise ValueError('complete unique host source pins required')
        for name, expected in records:
            if _sha(_file(area, name).read_bytes()) != expected:
                raise ValueError('host source or dependency changed')
    if dict(plan['python_files']).get('competition/deepeye/tools/run_owned_chain_headless.py') != _sha(Path(__file__).read_bytes()):
        raise ValueError('original runner not pinned')
    project = _inside(plan['project_path'], unit/'owned-projects')
    pins = dict(plan['project_files'])
    ordered = [[name, pins[name]] for name in sorted(pins)]
    if len(pins) != len(plan['project_files']) or _sha(json.dumps(ordered, ensure_ascii=False, separators=(',', ':')).encode()) != plan['source_bundle_sha256']:
        raise ValueError('complete sorted native project pin mismatch')
    output = _inside(plan['output_path'], unit/'native-runs')
    if output.exists():
        raise ValueError('fresh operation output required; no replay')
    engine = _inside(plan['engine_path'], root)
    if _sha(engine.read_bytes()) != ENGINE:
        raise ValueError('approved engine changed')
    catalog_raw = _inside(plan['source_catalog_path'], unit).read_bytes()
    if _sha(catalog_raw) != plan['source_catalog_sha256']:
        raise ValueError('independent source catalog changed')
    diagnostic = _json(_file(project, 'owned-input/diagnostic-case.json').read_bytes())
    if diagnostic != dict(withhold_first_publish_ack=False, edit_once_after_unlock=False):
        raise ValueError('synthetic action/edit fixture refused')
    if _file(project, 'owned-input/managed-writer-controls.json').exists():
        raise ValueError('managed actor fixture refused')
    if type(plan['sample_records']) is not int or not 2 <= plan['sample_records'] <= 16:
        raise ValueError('new causal source record count2..16 required')
    policy = _policy(project, _json(catalog_raw), pins, plan['source_bundle_sha256'], plan['run_id'])
    spec = native.ApprovedLaunchSpec(engine, ENGINE, project,
        tuple(tuple(pair) for pair in ordered), plan['source_bundle_sha256'],
        plan['raw_layout_sha256'], _inside(plan['stdout_path'], output),
        _inside(plan['stderr_path'], output), tuple(tuple(pair) for pair in plan['environment']),
        plan['run_id'], 20_000_000_000, 45_000_000_000)
    return unit, plan, release, spec, policy, _sha(plan_raw), _sha(release_raw)


def _pump(owner, predicate, deadline):
    while True:
        owner.poll()
        if owner._clock() >= deadline:
            raise TimeoutError('new original operation deadline expired')
        if owner._vetoed:
            raise ValueError('original world vetoed: '+str(owner._reason))
        if predicate():
            return
        time.sleep(.001)


def _complete(record):
    slots = record['slots']
    return ((slots['process']['state'] == 'NOT_ACQUIRED' or
        (record['wait_result'] == 0 and type(record['exit_code']) is int))
        and (slots['job']['state'] == 'NOT_ACQUIRED' or record['job_active_processes'] == 0)
        and all(slot['state'] in ('NOT_ACQUIRED', 'CLOSED') for slot in slots.values()))


def _close(owner, clock):
    history, deadline = [], None
    while True:
        record = owner.close('new initial-view/source operation complete; original cleanup')
        history.append(record)
        if (_complete(record) or
                any(slot['state'] in ('UNKNOWN', 'RELEASE_UNKNOWN') for slot in record['slots'].values())):
            return history
        # A failed action clock cannot suppress the first original cleanup.
        # If it remains unreadable, preserve the incomplete observation and
        # stop; no replacement clock, reopened process or unbounded loop.
        try:
            now = clock()
        except BaseException as error:
            history[-1] = dict(record, cleanup_clock_error=type(error).__name__)
            return history
        if deadline is None:
            deadline = now+5_000_000_000
        elif now >= deadline:
            return history
        time.sleep(.01)  # Same original observations; backend effects are once-only.


def run(plan_path, release_path):
    unit, plan, release, spec, policy, plan_sha, release_sha = _approved(plan_path, release_path)
    quota = unit/'native-launches'
    quota.mkdir(exist_ok=True)
    _save(quota/'slot-1.json', dict(operation_id=plan['operation_id'],
        plan_sha256=plan_sha, release_sha256=release_sha))
    output = Path(plan['output_path']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    clock = host_clock.qpc_clock_for_new_run()
    owner = source = initial = failed_native = None
    records, timings = [], []
    start = clock()
    overall_deadline = start+45_000_000_000
    result = dict(schema=1, work_id=WORK, operation_id=plan['operation_id'], mode=MODE,
        started_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=plan_sha,
        release_sha256=release_sha, component_complete=False, board=False, ADC=False,
        CPU_AI=False, movement_authorized=False, behavioral_STOP_proven=False,
        complete_H12='not_run', G03='not_run', R03='not_run', all29='not_run')
    try:
        owner = loop._acquire_root_world(spec, clock)
        _pump(owner, lambda: owner._hello is not None, min(overall_deadline, clock()+spec.startup_timeout_ns))
        owner.request_freeze(snapshot_limits_sha256=_sha(_raw(LIMITS)),
                             model_policy_sha256=values._digest(policy))
        _pump(owner, lambda: owner._state == 'FROZEN', overall_deadline)
        epoch = owner.frozen_epoch()
        with (output/'original-snapshot.json').open('xb') as stream:
            stream.write(epoch.snapshot_raw)  # Root private; never a controller input.
        pair = [gates.Gate(item.face, values._decode_bits(item.u_bits, 64),
                          values._decode_bits(item.v_bits, 64)) for item in epoch.snapshot.workspace.gates]
        pose = initial_pose_for_layout(workspace.Layout(*pair), standoff_m=plan['initial_standoff_m'])
        binding = owner.construct_and_bind(epoch, policy, initial_pose=pose)
        initial = owner.initialize_view(binding)
        _pump(owner, lambda: owner._initialized, min(overall_deadline, initial.deadline_ns))
        if (owner._commits or owner._diagnostic_used or initial.kind != 'INITIAL_VIEW'
                or initial.revision != 0 or not initial.resolved or initial.state != 'APPLIED'
                or initial.readback_ns is None or initial.readback_ns >= initial.deadline_ns):
            raise ValueError('actual initial view not accepted with zero numerical commits')
        result['initial_pose'] = asdict(pose)
        result['freeze_identity'] = epoch.identity
        result['inventory'] = asdict(epoch.snapshot.inventory_counts)
        result['constructor'] = dict(entry_ns=binding.constructor_entry_ns, exit_ns=binding.constructor_exit_ns)
        result['initial_view'] = dict(kind=initial.kind, operation_id=initial.operation_id,
            state=initial.state, revision=initial.revision, resolved=initial.resolved,
            readback_ns=initial.readback_ns, deadline_ns=initial.deadline_ns,
            actual_getter_differences=initial.differences,
            readback=initial.readback.as_dict())
        field = OwnedWorldField(binding.executor, **plan['field_policy'])
        source = CausalSourcePump(field.pose_reader, field.sample_sigma)
        source.prepare()
        origin = clock()
        source.start(origin, clock)
        payload = source.poll()  # First actual acquisition immediately, no backfill.
        while True:
            if clock() >= min(overall_deadline, origin+2_000_000_000):
                raise TimeoutError('new actual source budget expired; no restart')
            if payload is not None:
                records.append(payload)
                timings.append(clock())
            if len(records) == plan['sample_records']:
                break
            owner.poll()
            if owner._vetoed or owner._commits or owner._diagnostic_used:
                raise ValueError('original world retired or unexpected numerical action')
            time.sleep(.001)
            payload = source.poll()
        source.retire('new current-world source record budget completed')
        _save(output/'causal-source.json', dict(source_origin_qpc_ns=origin,
            actual_record_end_qpc_ns=timings, records=records,
            source_kind='candidate_nominal_field', source_revision=0,
            sensor_calibration_proven=False, ADC=False, movement_authorized=False))
        result['causal_source'] = dict(records=len(records), origin_qpc_ns=origin,
            actual_adc_ticks_ms=[item['adc_tick_ms'] for item in records],
            source_sha256=_sha((output/'causal-source.json').read_bytes()),
            same_original_executor=field._executor is binding.executor,
            same_original_scene=field._scene is binding.world_values.scene)
        result['source_complete'] = True
    except BaseException as error:
        result['error'] = dict(type=type(error).__name__, text=str(error)[:1024])
        if owner is None and isinstance(error, native.AcquisitionFailure):
            failed_native = error.owner  # Retain the exact failed acquisition.
            result['failed_original_native'] = failed_native.diagnostics()
            result['acquisition_cause'] = dict(type=type(error.cause).__name__,
                                             text=str(error.cause)[:1024])
    finally:
        if source is not None:
            result['partial_causal_records'] = records
            result['partial_causal_record_end_qpc_ns'] = timings
        if source is not None and source.state != 'RETIRED':
            try:
                source.retire('new world/source operation failed')
            except BaseException as error:
                result['source_retire_error'] = type(error).__name__
        if owner is not None:
            try:
                result['close_history'] = _close(owner, clock)
                result['owner'] = owner.evidence()
                final = result['close_history'][-1]
                result['native_resources_complete'] = _complete(final)
                result['original_cohort_closed'] = (_complete(final) and final['state'] == 'CLOSED'
                    and final['original_factory'] is True and not final['errors'])
                result['zero_numerical_commits'] = not owner._commits and owner._diagnostic_used is False
                result['component_complete'] = (result.get('source_complete') is True
                    and result['original_cohort_closed'] and result['zero_numerical_commits']
                    and 'error' not in result)
            except BaseException as error:
                result['cleanup_error'] = dict(type=type(error).__name__, text=str(error)[:1024])
        elif failed_native is not None:
            try:
                result['failed_native_close_history'] = _close(failed_native, clock)
                result['failed_original_native'] = failed_native.diagnostics()
                result['native_resources_complete'] = _complete(result['failed_original_native'])
            except BaseException as error:
                result['cleanup_error'] = dict(type=type(error).__name__, text=str(error)[:1024])
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        _save(output/'result.json', result)
        _save(quota/'slot-1-terminal.json', dict(operation_id=plan['operation_id'],
            result_sha256=_sha((output/'result.json').read_bytes()),
            original_cohort_closed=result.get('original_cohort_closed') is True,
            component_complete=result['component_complete'], movement_authorized=False))
    return 0 if result['component_complete'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    return run(args.plan, args.release)


if __name__ == '__main__':
    raise SystemExit(main())
