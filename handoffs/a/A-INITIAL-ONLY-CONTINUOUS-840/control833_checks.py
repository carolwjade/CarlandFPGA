"""Two new pure controls only. AST slices avoid controller/dependency execution.

The slider control catches 808's ongoing cap / invalidation bug. The display
control catches a telemetry sharing violation escaping into the control loop.
No board, native app, sensor, model, network, real worker or controller main runs.
"""
import ast
import copy
import hashlib
import json
import math
import pathlib
import sys
import time
from types import SimpleNamespace


def namespace(tree):
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                and n.name != 'main']
    ns = dict(math=math, json=json, hashlib=hashlib, time=time)
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pure833-definitions>', 'exec'), ns)
    return ns


def test_slider_after_latch_preserves_current_control(tree):
    ns = namespace(tree)
    current_advice = dict(status='ADVISE', speed_limit_m_s=.075)
    current_desired = dict(yaw_q=13, pitch_q=-7, speed_code=6, reason='actual_ai')
    ns.update(operator_seq=1, operator_generation=4, advice=current_advice,
              desired=current_desired, speed_cap=.25, paused=False, want_stop=False,
              epoch='fresh-833', op_path=SimpleNamespace(exists=lambda: True),
              log=lambda *args, **kw: None, display=lambda **kw: None)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    block = next(n for n in ast.walk(main) if isinstance(n, ast.If)
                 and isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Attribute)
                 and n.test.func.attr == 'exists' and isinstance(n.test.func.value, ast.Name)
                 and n.test.func.value.id == 'op_path')
    code = compile(ast.Module(body=[block], type_ignores=[]), '<actual-operator-block>', 'exec')
    control = ns.get('RunControl', lambda: None)()
    if control is not None:
        control.initial_request = .1
        control.next_initial_preference = .1
        control.operator_seq = 1
        control.operator_generation = 4
        reserved = control.reserve_initial()
        # A slider race during the first in-flight APPLY changes only next-run storage.
        control.accept(dict(action='set_initial_speed', requested_speed_m_s=.2,
                            requested_paused=True, seq=2, epoch='fresh-833'), 'fresh-833')
        assert reserved == .1 and control.initial_request == .1
        assert control.speed_limit() == .1 and control.next_initial_preference == .2
        assert control.operator_generation == 4 and control.paused is False
        control.consume_initial(reserved)
        assert control.initial_speed_latched and control.latched_initial_speed == .1
        control.operator_seq = 2
        control.advice = current_advice
        control.desired = current_desired
        ns['control'] = control
    for seq, action, value in ((3, 'next_initial_speed', 0.), (4, 'set_speed', .25),
                               (5, 'set_initial_speed', .0125)):
        op = dict(action=action, requested_speed_m_s=value, requested_paused=True,
                  seq=seq, epoch='fresh-833', world_epoch='fresh-833',
                  actual_board_action_performed=False, stop_latched=False)
        ns['load'] = lambda path, op=op: op
        exec(code, ns)
        if control is None:
            assert ns['advice'] is current_advice, 'slider invalidated current advice'
            assert ns['desired'] is current_desired, 'slider changed desired intent'
            assert ns['operator_generation'] == 4 and ns['speed_cap'] == .25
        else:
            assert control.advice is current_advice and control.desired is current_desired
            assert control.operator_generation == 4 and control.speed_limit() == .25
            assert control.paused is False and control.initial_request == .1
            assert control.latched_initial_speed == .1 and control.next_initial_preference == value
            visible = control.status_fields()
            assert visible['operator_state'] == 'next_initial_stored'
            assert visible['operator_ack_seq'] == seq
            assert visible['operator_control_ack_seq'] != seq
            control.acknowledge_apply(4, 1, current_desired)
            assert control.status_fields()['operator_state'] == 'next_initial_stored'
            assert control.status_fields()['operator_ack_seq'] == seq
            assert control.status_fields()['operator_control_ack_seq'] == 1
    if control is not None:
        preference = control.next_initial_preference
        control.accept(dict(action='pause', requested_speed_m_s=.2,
                            requested_paused=True, seq=6, epoch='fresh-833'), 'fresh-833')
        control.accept(dict(action='resume', requested_speed_m_s=.2,
                            requested_paused=False, seq=7, epoch='fresh-833'), 'fresh-833')
        assert control.initial_speed_latched and control.latched_initial_speed == .1
        assert control.next_initial_preference == preference and control.speed_limit() == .25
        assert control.advice is None and control.desired is None and control.awaiting_resume_ai
        zero = ns['RunControl'](0.)
        zero.consume_initial(zero.reserve_initial())
        assert zero.initial_speed_latched and zero.latched_initial_speed == 0.
        assert zero.speed_limit() == .25 and not zero.paused


def test_display_permission_error_does_not_escape_control(tree):
    ns = namespace(tree)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    display = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'display')
    calls = []
    def denied(*args):
        raise PermissionError(13, 'injected Godot read/share-delete race')
    ns.update(visible=dict(actual_speed_m_s=.075), epoch='fresh-833', operation_id='A-NEW-833',
              status=pathlib.Path('host-status.json'), atomic=denied,
              log=lambda event, **fields: calls.append(dict(event=event, **fields)))
    if 'RunControl' in ns:
        ns['control'] = ns['RunControl']()
    exec(compile(ast.Module(body=[copy.deepcopy(display)], type_ignores=[]),
                 '<actual-display-function>', 'exec'), ns)
    ns['display'](stage='still-controlling')
    assert ns['visible']['actual_speed_m_s'] == .075
    assert len(calls) == 1 and calls[0]['event'] == 'display-publication-delayed'
    # Publication is attempted again only on the next ordinary call, with latest data.
    published = []
    ns['atomic'] = lambda path, value: published.append(copy.deepcopy(value))
    ns['display'](sample_count=143)
    assert len(published) == 1 and published[0]['sample_count'] == 143
    assert published[0]['stage'] == 'still-controlling'
    # The telemetry boundary must not swallow a critical journal write failure.
    ns['atomic'] = denied
    def journal_failed(*args, **kw):
        raise OSError('critical journal write failed')
    ns['log'] = journal_failed
    try:
        ns['display']()
    except OSError as exc:
        assert 'critical journal' in str(exc)
    else:
        raise AssertionError('critical journal error was hidden')


if __name__ == '__main__':
    path = pathlib.Path(sys.argv[1])
    tree = ast.parse(path.read_bytes(), filename=str(path))
    results = []
    for test in (test_slider_after_latch_preserves_current_control,
                 test_display_permission_error_does_not_escape_control):
        try:
            test(tree)
            results.append(dict(name=test.__name__, passed=True))
        except Exception as exc:
            results.append(dict(name=test.__name__, passed=False,
                                error=type(exc).__name__ + ': ' + str(exc)))
    report = dict(source=str(path), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  ast='passed', controls=results, passed=sum(v['passed'] for v in results),
                  total=2, actual_controller_execution=False,
                  board_native_model_sensor_network_execution=False)
    if len(sys.argv) > 2:
        pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] == 2 else 1)
