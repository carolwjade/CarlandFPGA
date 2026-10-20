import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
a=json.loads((D/'final-audit.json').read_bytes());c=json.loads((D/'cleanup-current.json').read_bytes());assert not c['known_pids_still_live']and not c['subst_lines']and c['accidental_unowned_temp_absent']
assert a['fresh_checker_errors']==0 and a['source_unchanged_after_runs']and a['own_all_commands_exited_without_timeout']
save(D/'preparation-failures.json',{'audit_attempt01':{'command':'.local/venv/Scripts/python.exe -B -X utf8 .planning/deepeye-resume-20261018/b-op15-independent-20261020/audit.py','exit':1,'error':'FileNotFoundError: wrong ROOT parent index resolved .planning/docs/competition/deepeye-2026/immutable_scope.json; corrected before successful audit'},'launch_attempt01':{'receipt':'receipt.json','actual_simulator_exit':0,'actual_stderr':'Error: can\'t read "FileWatch(fileName)": no such element in array','claim':'rejected; no TB trace completion'},'attempt02':{'receipt':'attempt02/receipt.json','outer_exec_session':55084,'outer_exit':1,'interruption':'Ctrl-C after detected huge maximum-width vector preparation; no maximum-width simulator launched','loopback_expectation_failure':'source switched to loopback after application baseline; actual incoherent fault, corrected source held through application','cleanup':'R mapping removed explicitly; no recorded/review process remains in cleanup-current.json'},'scope_deviation':{'path':'.planning/deepeye-resume-20261018/recheck_unused.tmp','content':'unused\n','bytes':7,'effect':'new temporary file accidentally created outside ownership then immediately removed','current_absent':c['accidental_unowned_temp_absent']}})
summary={
 'job_id':'child-9892f349e0d047688cebdc5a85ceb8fa','agent':'/root/b_op15_review_20261020',
 'status':'bounded independent review complete; two residual runner parser findings reported; quality main retains acceptance',
 'head':'df82af1bc91d01aeb9adee19f48c0890dfc1ac5b','source':'52dc249c529b92a7b6be06550db5e7203c5c5a42',
 'operation':'B-DEEPEYE-PWM-APPLIED-CAPTURE-20261020-15','source_unchanged':True,
 'fresh_edges':4472,'fresh_handshakes':173,'fresh_check_errors':0,'fresh_guards':9,'fresh_mutant_copies':4,
 'open_findings':['R15-PARSER-SUBSTRING: completed exit0 plus NOT_TB_PASS_MARKER and zero stats is accepted','R15-PARSER-MULTISTATS: completed exit0 plus PASS and conflicting zero/nonzero stats rows is accepted'],
 'observed_actual_run_not_exploiting_synthetic_findings':True,
 'all29_formal':'not_run','evidence_hashes':{p:sha(D/p)for p in ['final-audit.json','findings.md','cleanup-current.json','qualification-summary.json','command-ledger-recheck.json','attempt03/receipt.json','mutant-runs/receipt.json','same-tag-probe/receipt.json','preparation-failures.json']}}
save(D/'review-report.json',summary)
text=f'''Bounded independent B op15 review complete; evidence only, quality main retains acceptance.
Job child-9892f349e0d047688cebdc5a85ceb8fa; agent /root/b_op15_review_20261020.
Task DEEPEYE-IMPLEMENTATION-20261014/v1, sole A Desktop director 01a13d7e-dcf1-7272-a738-a637dd62ff9d generation2.
H01-H15 DEEPEYE-HUMAN-LOCK-20261014/revision1 canonical requirements c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804 verified.
B head df82af1bc91d01aeb9adee19f48c0890dfc1ac5b; source 52dc249c529b92a7b6be06550db5e7203c5c5a42; operation B-DEEPEYE-PWM-APPLIED-CAPTURE-20261020-15; request564729a70a21b5ff71526b85958f6a113a50e7943ae0ed07a72d976723d39272; manifest331e7fcc5971ea61208bc052efa430be7ed4dc802037198a4975df6040290ba9.
All1773 handoff entries/1795 selected files verified by size/SHA256 and all selected Git blobs; source unchanged afterward. Immutable op12/op14 RTL hashes match reviewed dependencies; broad campaigns reused without rerun.
Actual ModelSim SE-64 2020.4 exact-DUT compile and three fresh configurations 4:8:8,2:2:1,32:64:64 produced4472 edges/173 handshakes/558 pre/post valid observations, zero independent checker discrepancies. No B model/runner/vector import. Public history verifies actual-application tuple/tag and complete post-baseline common-rise/first-fall/common-rise sample interval; transfer/pending/repeated-tag/reset/STOP/backpressure/failure/recovery and zero/full-high exclusions covered. A later public accepted-command ledger rechecked saved traces with zero discrepancies; chronology disclosed.
Nine actual guards each produce exact time-zero DUT fatal despite exit0. Three compiled isolated mutants rejected with2/84/12 checker violations. Additional same-tag binding-retention probe gives184 violations including forbidden old handshakes at631/674/826/859; all mutant simulations complete, so these are behavioral rejections, not compiler failures.
Original runner reproduces13/16 qualification failures; repaired83f192c70ab48427e70a0dc66662e4a24a66be90633a454a82e179a6a79ddf98 passes original16. Two NEW residual synthetic parser defects remain: substring NOT_TB_PASS_MARKER qualifies, and first zero TB_STATS hides a later conflicting nonzero row. Exact fixtures retained; no product source repair performed. Do not claim unconditional strict runner qualification without main disposition.
Actual repaired47-command logs independently hash/marker/diagnostic reconciled:19 positive scenarios/208667 samples/100587 assertions/476 records/459 handshakes,9 exact guards,4 intended behavioral mutant rejections+1 faulty code7 demonstration. Actual saved logs do not exploit the two new synthetic gaps. Preserved B main492440edges/83462RLE vector/log totals and command hashes reconcile as historical evidence, without importing its oracle.
Original red runner, debug/compiler failures, post-hoc g15-b context, manifest-race originals and prior op13/op14 missing-history limitations remain preserved/disclosed. Own initial ROOT error, exit0 Tcl launch error, corrected loopback stimulus and interrupted huge vector preparation are disclosed. A tool-call mistake created a7-byte unowned recheck_unused.tmp then immediately removed it; absence verified, deviation disclosed and not authorized retroactively.
57 raw owned tool/mapping command records have actual terminal exits/no timeout. Fresh cleanup finds no recorded process/review simulator or private mapping. No product/board/GUI/services/drivers/config/credentials/install/Git/external messages/children operations; private lease never displayed.
All29 formal cards/G05/B06/R03 not_run. No synthesis,implementation,CDC/RDC,physical capture/timing,max32/max64 traversal,ABI/BOOT/TTL,freshness/motion authority or full product chain grant.
Evidence directory: {D}
review-report.json SHA256 {sha(D/'review-report.json')}
final-audit.json SHA256 {sha(D/'final-audit.json')}
findings.md SHA256 {sha(D/'findings.md')}
'''
(D/'final-result.txt').write_text(text,encoding='utf8')
exclude={'lease.private.json','manifest.json','native-complete-response.json','final-check.json'}
records={p.relative_to(D).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(D.rglob('*'))if p.is_file()and p.relative_to(D).as_posix()not in exclude}
save(D/'manifest.json',{'scope':'owned review evidence; excludes private lease, own manifest and post-completion response/check','files':records})
print(json.dumps({'files':len(records),'final_result_sha256':sha(D/'final-result.txt'),'review_report_sha256':sha(D/'review-report.json'),'manifest_sha256':sha(D/'manifest.json')}))
