import hashlib,json,pathlib,shutil,subprocess
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];P=ROOT/'.local/deepeye-implementation-a';AUTHOR=H.parent/'actor-owner-implementation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(AUTHOR/'source-manifest.json')=='2bace7921cd89ff2cf7e9d1dd8b87dbd1be6f4d34abd1ac3cc3d37026dc39630'
assert sha(AUTHOR/'report.md')=='d1f0cf6f275b8ddbc4ac127e08f915fe7e32c1c8836678c9ac4b6b3fd0a91ed8'
assert sha(AUTHOR/'receipt.json')=='bd8bf32d56d756d717976053c102726fcf58c03a6a7bd704659ba608182701c5'
assert sha(H.parent/'ai-lifetime-design/design.md')=='5eb4fd822d9e30a9ca032de7a9fca969ab24e1751558bb922f654032165cbb4f'
terminal=json.loads((AUTHOR/'native_completion.json').read_text());assert terminal['status']=='completed' and terminal['terminal'] is True
m=json.loads((AUTHOR/'source-manifest.json').read_text());git=shutil.which('git') or 'C:/Program Files/Git/cmd/git.exe'
out={'candidate':[],'files':{},'commands':[]}
head=subprocess.run([git,'rev-parse','HEAD'],cwd=P,capture_output=True);assert head.returncode==0
out['head']=head.stdout.decode().strip();assert out['head']=='3f702903f1e16fa72eae15f03ba431b78de24bd0'
for entry in m['files']:
    rel=entry['path'];p=P/rel;frozen=AUTHOR/'candidate'/rel
    assert sha(p)==sha(frozen)==entry['sha256']
    raw=subprocess.run([git,'hash-object','--stdin'],input=p.read_bytes(),cwd=P,capture_output=True)
    clean=subprocess.run([git,'hash-object','--path='+rel,'--stdin'],input=p.read_bytes(),cwd=P,capture_output=True)
    assert raw.returncode==clean.returncode==0
    assert raw.stdout.decode().strip()==entry['raw_git_object']==clean.stdout.decode().strip()==entry['clean_git_object']
    target=H/'frozen'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    out['candidate'].append(entry);out['files'][str(p)]=sha(p)
for rel,h in m['dependencies'].items():
    if rel=='requirements':continue
    p=P/'competition/deepeye'/rel;assert sha(p)==h;out['files'][str(p)]=h
for rel in ['integration/host_envelope.py','integration/pc_direct_watchdog.py','integration/clock_bounds.py','integration/host_timing_contract.json']:
    p=P/'competition/deepeye'/rel
    if p.is_file():out['files'][str(p)]=sha(p)
for p in [ROOT/'.agents/skills/fpga-multi-node/SKILL.md',ROOT/'.agents/skills/fpga-multi-node/skill-role.json',ROOT/'.agents/skills/fpga-multi-node/references/protocol.md',ROOT/'.planning/deepeye-desktop-handoff-20261015/transfer.json',P/'AGENTS.md',P/'docs/competition/deepeye-2026/immutable_scope.md',P/'docs/competition/deepeye-2026/immutable_scope.json',P/'docs/competition/deepeye-2026/taskbook_final.md',P/'docs/competition/deepeye-2026/execution_plan_final.json']:
    p.read_text(encoding='utf-8-sig');out['files'][str(p)]=sha(p)
lock=json.loads((P/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
req=hashlib.sha256(json.dumps(lock['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert req==m['dependencies']['requirements']=='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
out['requirements_sha256']=req
(H/'before.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'head':out['head'],'candidate_files':len(out['candidate']),'source_dependency_files':len(out['files']),'canonical_requirements_sha256':req,'author_terminal':'completed/true','live_frozen_clean_parity':True},indent=2))
