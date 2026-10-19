import hashlib,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CROOT=Path('C:/Users/CarlJade/.codex/worktrees/deepeye-c-pr25-review/FPGA多机协作开发')
HEAD='942fa309ffc8f1d32c816cfa643b009b031d7d0a'
PIN='c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git','-c','core.longpaths=true','-C',str(CROOT),*a])
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert not git('status','--porcelain=v1')
for base in (ROOT,CROOT):
 d=json.loads((base/'docs/competition/deepeye-2026/immutable_scope.json').read_text(encoding='utf-8-sig'))
 assert sha(json.dumps(d['requirements'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==PIN
 assert [r['id'] for r in d['requirements']]==['H%02d'%i for i in range(1,16)]
ops=[('C-DEEPEYE-REVIEWFIXES-20261018-12','216270732b1045fbb5eddcbe3f34dfe44df1432a41bfde11b88fd01b19edcaee','ac9671977fa3e3cab5f81a63cdfd5edb06eb7437bfc85812c19b37496d6ab220'),('C-DEEPEYE-TRACE-CANDIDATE-DECODE-20261018-14','85e2aac41409988a6f0704d438b6a583d6de6530b95052e34cbd82df6df4fa9a','3102d6d5e65dad3dfc6dba65eea465d7ac91816a65413d36b8825e2e71eb800e')]
manifests={}; specs=[]
for op,msha,rsha in ops:
 path='handoffs/c/'+op+'/manifest.json'; raw=git('show',HEAD+':'+path); assert sha(raw)==msha
 m=json.loads(raw);assert m['request_hash']==rsha
 assert sha(json.dumps(m['request'],sort_keys=True,separators=(',',':')).encode())==rsha
 assert set(m['artifacts'])==set(m['files'])
 (OUT/(op+'.manifest.exact.json')).write_bytes(raw)
 manifests[op]=m
 for rel in m['files']:
  assert not rel.lower().endswith(('.las','.laz','.zip'))
  specs.extend([HEAD+':'+rel,m['request']['code_commit']+':'+rel])
p=subprocess.run(['git','-C',str(CROOT),'cat-file','--batch'],input=('\n'.join(specs)+'\n').encode(),capture_output=True,check=True)
buf=p.stdout; offset=0; blobs=[]
for spec in specs:
 end=buf.index(b'\n',offset); header=buf[offset:end].split(); assert header[1]==b'blob',spec
 size=int(header[2]); b=buf[end+1:end+1+size];assert buf[end+1+size:end+2+size]==b'\n';offset=end+2+size
 blobs.append((header[0].decode(),b))
rows={}; summaries={};idx=0
for op,m in manifests.items():
 for rel,expect in m['files'].items():
  oid,b=blobs[idx];sourceoid,sourceb=blobs[idx+1];idx+=2
  assert b==sourceb and sha(b)==expect['sha256'] and len(b)==expect['size'],rel
  checkout=(CROOT/rel).read_bytes();dest=OUT/'exact-git-blobs'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert dest.read_bytes()==b
  else:dest.write_bytes(b)
  rows[rel]={'blob':oid,'source_blob':sourceoid,'sha256':sha(b),'size':len(b),'checkout_sha256':sha(checkout),'checkout_exact':checkout==b,'only_line_endings_differ':checkout.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n')}
 summaries[op]={'artifacts':len(m['files']),'request':m['request'],'stages':m['stages']}
save('before.json',{'head':HEAD,'clean':True,'requirements_sha256':PIN,'files':rows})
save('manifest-verification.json',{'head':HEAD,'operations':summaries,'unique_artifacts':len(rows),'all_source_head_blobs_equal':True,'checkout_differences':[k for k,v in rows.items() if not v['checkout_exact']]})
print(json.dumps({'head':HEAD,'counts':{k:v['artifacts'] for k,v in summaries.items()},'unique':len(rows),'request_summaries':summaries},ensure_ascii=False))
