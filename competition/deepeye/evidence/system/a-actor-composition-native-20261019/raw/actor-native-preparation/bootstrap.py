import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a'
rels=['competition/deepeye/simulation/isolation/actor_fixture.py','competition/deepeye/tests/isolation/test_actor_windows_live.py','competition/deepeye/docs/actor_native_probe.md']
assert not any((P/r).exists() for r in rels),'NEW ownership already occupied'
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert req=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
paths=[ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json',P/'docs/competition/deepeye-2026/immutable_scope.md',P/'docs/competition/deepeye-2026/immutable_scope.json',H.parent/'actor-owner-review/findings.md',H.parent/'actor-owner-review/manifest.json',P/'competition/deepeye/simulation/isolation/prototype.py',P/'competition/deepeye/simulation/isolation/policy.py']
out={'requirements_sha256':req,'new_paths_absent':rels,'reference_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'concurrent_repair_final_manifest':'not yet bound; do not execute','native':'not_run'}
(H/'before.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'requirements_sha256':req,'new_paths_absent':3,'native':'not_run'}))
