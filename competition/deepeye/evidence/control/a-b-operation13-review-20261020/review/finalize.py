"""Seal public evidence without including the private lease input."""
import datetime,hashlib,json,pathlib
P=pathlib.Path(__file__).absolute().parent
R=P.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert json.loads((P/'audit-result.json').read_bytes())['status']=='reconciled'
put(P/'outer-launch-evidence.json',{
  'review': {'argv':[str(R/'.local/venv/Scripts/python.exe'),'-B','-X','utf8',str(P/'review.py')],
             'cwd':str(R),'execution_session_id':9295,'completion_tool_chunk':'e433a1','actual_exit_code':0,
             'stdout':{'status':'bounded_independent_simulation_passed','sampled_edges':1253606,'rle_rows':79247,'small_width_legal_pairs':129,'source_unchanged':True,'mapping_removed':True}},
  'audit': {'argv':[str(R/'.local/venv/Scripts/python.exe'),'-B','-X','utf8',str(P/'audit.py')],
            'cwd':str(R),'completion_tool_chunk':'6039ba','actual_exit_code':0,'status':'reconciled'},
  'launch_records_source':'actual exec_command/write_stdin tool results, copied without secrets',
  'confidentiality_exception':'Initial full lease read exposed the private token in tool output; token absent from authored public artifacts. No credential/provider changes attempted.'})
skip={'lease.private.json','evidence-manifest.json','native-completion.json','terminal-hashes.json'}
files={str(f.relative_to(P)).replace('\\','/'):{'bytes':f.stat().st_size,'sha256':sha(f)}
       for f in sorted(P.rglob('*')) if f.is_file() and f.name not in skip}
put(P/'evidence-manifest.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'work_id':'A-B-OP13-INDEPENDENT-20261020-v1','files':files,
    'exclusions':sorted(skip),'private_lease_input_not_for_publication':True})
print(json.dumps({'file_count':len(files),'hashes':{f:sha(P/f) for f in ['findings.md','receipt.json','audit-result.json','evidence-manifest.json']}},ensure_ascii=False))
