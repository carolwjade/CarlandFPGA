"""Untrusted CPU probe. Runs in the container and only attacks its own fixtures."""
import _winapi as K
import json
import sys

def main():
    model, truth, parent, excluded, input_handle, output_handle = sys.argv[1:]
    parent, excluded, input_handle, output_handle = map(int, (parent, excluded, input_handle, output_handle))
    result = {'model_ok': False, 'pipe_ok': False, 'process_access_errors': {}}
    with open(model, encoding='utf-8') as stream:
        weights = json.load(stream)['weights']
    inferred = sum(w * x for w, x in zip(weights, (1, 2, 3)))
    result['model_ok'] = weights == [2, 3, 5] and inferred == 23
    result['cpu_output'] = inferred
    data, error = K.ReadFile(input_handle, 256)
    result['pipe_ok'] = error == 0 and data == b'authorized-causal-observation-v1\n'
    K.WriteFile(output_handle, json.dumps({'phase': 'positive_controls', 'result': result}).encode('ascii') + b'\n')
    try:
        handle = K.CreateFile(truth, 0x80000000, 7, 0, 3, 0x80, 0)
    except OSError as error:
        result['truth_open_error'] = error.winerror
    else:
        result['truth_open_error'] = 0
        K.CloseHandle(handle)
    for access in (8, 16, 32, 64, 128):
        try:
            handle = K.OpenProcess(access, False, parent)
        except OSError as error:
            result['process_access_errors'][str(access)] = error.winerror
        else:
            result['process_access_errors'][str(access)] = 0
            K.CloseHandle(handle)
    K.WriteFile(output_handle, json.dumps({'phase': 'boundaries', 'result': result}).encode('ascii') + b'\n')
    K.WriteFile(output_handle, json.dumps({'phase': 'excluded_handle_attempt', 'handle': excluded}).encode('ascii') + b'\n')
    try:
        K.ReadFile(excluded, 256)
    except OSError as error:
        result['canary_handle_error'] = error.winerror
    else:
        result['canary_handle_error'] = 0
    raw = json.dumps({'phase': 'complete', 'result': result}, sort_keys=True).encode('ascii') + b'\n'
    if len(raw) > 4096:
        raise RuntimeError('fixture output exceeded protocol limit')
    count, error = K.WriteFile(output_handle, raw)
    if error or count != len(raw):
        raise RuntimeError(f'WriteFile incomplete: {count}, {error}')


if __name__ == '__main__':
    main()
