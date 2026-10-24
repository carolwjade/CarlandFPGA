# TEST-ONLY loss adapter; not production helper.
import hashlib, json, os, struct, sys, time, types
def exact(n):
    data=b''
    while len(data)<n:
        chunk=sys.stdin.buffer.read(n-len(data))
        if not chunk: raise ValueError('short')
        data+=chunk
    return data
assert exact(4)==b'DLC1'
n=struct.unpack('>I',exact(4))[0]
assert 0<n<=4096
meta=json.loads(exact(n).decode('utf-8'))
payload=exact(meta['payload_bytes'])
assert hashlib.sha256(payload).hexdigest()==meta['payload_sha256']
root=os.path.dirname(__file__)
with open(os.path.join(root,'layout_commit_windows.py'),'rb') as f: leaf_raw=f.read()
assert hashlib.sha256(leaf_raw).hexdigest()=='521cfcea011d462b4b69641f33fbb6f3f7baca16eac7bb4e0b9ee8f1d932ed1f'
leaf=types.ModuleType('_test_only_checked_leaf');leaf.__file__=os.path.join(root,'layout_commit_windows.py')
exec(compile(leaf_raw,leaf.__file__,'exec'),leaf.__dict__)
result=leaf.commit_new(meta['target'],payload)
assert result['state']=='committed'
time.sleep(30) # watchdog124 after real publication; response intentionally lost

