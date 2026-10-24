"""Read only original live ownership; no native call, reopening, or cleanup."""
from dataclasses import asdict
assert len(case_results)==3 and not case_errors
rows=[]
for case,ctx in case_results.items():
    a=ctx.actor
    allow=json.loads((ctx.directory/'allow.json').read_bytes())
    snap=probe._snapshot(ctx)
    stage={p.relative_to(a._stage).as_posix():digest(p) for p in sorted(a._stage.rglob('*')) if p.is_file()}
    profile_path=a._resources.profile_path
    row={'case':case,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'context_retained_by_attempts':any(c is ctx for c in probe._ATTEMPTS),
         'registry_retains_exact_actor':any(o is a for o in ctx.registry._owners),
         'snapshot_unchanged':snap==ctx.cleanup,'snapshot':snap,
         'profile_delete_hresult':a._backend.profile_delete_hresult,
         'profile_absence_observed_by_original_backend':a._backend.profile_absence,
         'original_profile_path':str(profile_path),'original_profile_path_currently_absent':not Path(profile_path).exists(),
         'copied_runtime_directory':str(a._stage),'copied_runtime_hashes':stage,
         'copied_runtime_equals_approved_stage':stage==allow['staged_files'],
         'source_hashes_unchanged':all(digest(PRODUCT/n)==h for n,h in allow['sources'].items()),
         'original_primary_retained':(ctx.primary is a._primary_error) if case=='persistence-after-acquisition' else ctx.primary is None,
         'original_primary':None if ctx.primary is None else {'type':type(ctx.primary).__name__,'message':str(ctx.primary)},
         'registry_owner_count':len(ctx.registry._owners),'unresolved':ctx.unresolved,
         'resources_all_confirmed':all(r.outcome is not None and r.outcome.value=='confirmed' and r.attempted and not r.ambiguous for r in a._resources.references),
         'owner_errors':[asdict(e) for e in a._resources.errors],
         'evidence_complete':not a._evidence_errors}
    rows.append(row)
modules={}
for name,module in list(sys.modules.items()):
    filename=getattr(module,'__file__',None)
    if name.startswith('competition.deepeye.') and filename and Path(filename).is_file():
        modules[name]={'path':str(Path(filename).resolve()),'sha256':digest(Path(filename))}
record={'readback_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'interpreter_session_id':48521,
        'method':'Read retained exact objects and original backend outcomes; filesystem-only stage/profile/source readback. No OS resource reopened, no cleanup replay.',
        'retained_contexts':len(probe._ATTEMPTS),'retained_case_count':len(case_results),'cases':rows,'imported_modules':modules,
        'scope':'three Windows CPU actor lifecycle fixtures; expected negative failures retained; no real AI/BOOT/Run/board','formal29':'not_run'}
with (HERE/'retained-main-readback.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
assert len(rows)==3 and all(all(r[k] is True for k in ('context_retained_by_attempts','registry_retains_exact_actor','snapshot_unchanged','profile_absence_observed_by_original_backend','original_profile_path_currently_absent','copied_runtime_equals_approved_stage','source_hashes_unchanged','original_primary_retained','resources_all_confirmed')) and r['unresolved'] is False and r['owner_errors']==[] for r in rows)
print(json.dumps({'retained_readback_sha256':digest(HERE/'retained-main-readback.json'),'cases':len(rows),'all_original_resources_resolved':True,'profiles_absent':True,'copied_runtime_bytes_match':True,'interpreter_keeps_contexts_for_independent_review':True}))
