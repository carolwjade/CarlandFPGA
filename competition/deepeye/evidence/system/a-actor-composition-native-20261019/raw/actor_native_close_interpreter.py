"""Close only the fully resolved dedicated fixture interpreter; no cleanup replay."""
selection=json.loads((OUT/'actor-native-main-selection.json').read_bytes())
assert selection['resources_confirmed']==54 and selection['dedicated_interpreter']['main_thread_ends'] is False
assert len(case_results)==len(probe._ATTEMPTS)==3 and not case_errors
assert all(c.passed is True and c.unresolved is False and probe._snapshot(c)==c.cleanup for c in case_results.values())
assert all(any(o is c.actor for o in c.registry._owners) and c.cleanup['resources_complete'] is True and c.actor._backend.profile_absence is True and not Path(c.actor._resources.profile_path).exists() for c in case_results.values())
record={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'session_id':48521,'main_selection_sha256':digest(OUT/'actor-native-main-selection.json'),'original_contexts_rechecked':3,'resource_references_confirmed':54,'unresolved_resources':0,'cleanup_replayed':False,'native_handles_reopened':False,'primary_errors_and_failed_receipts':'preserved in frozen evidence; no successful receipt rewrite','dedicated_interpreter_exit_requested':0,'main_desktop_thread_retained':True}
with (HERE/'interpreter-exit-intent.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
print('DEDICATED_FIXTURE_INTERPRETER_RESOLVED_EXIT0; main Desktop thread retained')
raise SystemExit(0)
