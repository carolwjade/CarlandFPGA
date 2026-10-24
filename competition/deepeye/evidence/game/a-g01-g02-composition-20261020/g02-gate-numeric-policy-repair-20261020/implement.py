from pathlib import Path
import shutil,difflib
HERE=Path(__file__).resolve().parent;SIM=HERE/'stage/competition/deepeye/simulator'
shutil.copyfile(HERE/'gate_numeric.gd',SIM/'editor/gate_numeric.gd')
shutil.copyfile(HERE/'gate_json_numbers.gd',SIM/'editor/gate_json_numbers.gd')
for name in ['scene_document.gd','layout_codec.gd']:
 p=SIM/'editor'/name;s=(HERE/'baseline/editor'/name).read_text(encoding='utf-8')
 s=s.replace('extends RefCounted','extends RefCounted\n\nconst GateNumericScript = preload("res://editor/gate_numeric.gd")',1)
 if name=='scene_document.gd':
  s=s.replace('absf(float(gate.u)) > limit + 0.000000001 or absf(float(gate.v)) > limit + 0.000000001','not GateNumericScript.valid_coordinate(float(gate.u)) or not GateNumericScript.valid_coordinate(float(gate.v))')
  s=s.replace('separation < MIN_SAME_FACE_SEPARATION_M - 0.000000001','GateNumericScript.circles_overlap(float(gates.entry.u), float(gates.entry.v), float(gates.exit.u), float(gates.exit.v))')
 else:
  s=s.replace('const GateNumericScript = preload("res://editor/gate_numeric.gd")','const GateNumericScript = preload("res://editor/gate_numeric.gd")\nconst GateJsonNumbersScript = preload("res://editor/gate_json_numbers.gd")')
  s=s.replace('\tvar field_error := _check_fields(data, TOP_FIELDS, "文件")','\tvar restored_numbers: Dictionary = GateJsonNumbersScript.restore(text, data)\n\tif not restored_numbers.ok:\n\t\treturn _fail(String(restored_numbers.reason))\n\tvar field_error := _check_fields(data, TOP_FIELDS, "文件")',1)
  s=s.replace('absf(float(gate.u)) > GATE_EDGE_LIMIT + EPSILON or absf(float(gate.v)) > GATE_EDGE_LIMIT + EPSILON','not GateNumericScript.valid_coordinate(float(gate.u)) or not GateNumericScript.valid_coordinate(float(gate.v))')
  s=s.replace('separation < MIN_SAME_FACE_SEPARATION - EPSILON','GateNumericScript.circles_overlap(float(gates.entry.u), float(gates.entry.v), float(gates.exit.u), float(gates.exit.v))')
 p.write_text(s,encoding='utf-8')
 c=HERE/'candidate/editor'/name;c.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,c)
 base=(HERE/'baseline/editor'/name).read_text(encoding='utf-8')
 (HERE/(name+'.diff')).write_text(''.join(difflib.unified_diff(base.splitlines(True),s.splitlines(True),fromfile='a/editor/'+name,tofile='b/editor/'+name)),encoding='utf-8')
shutil.copyfile(HERE/'gate_numeric.gd',HERE/'candidate/editor/gate_numeric.gd')
shutil.copyfile(HERE/'gate_json_numbers.gd',HERE/'candidate/editor/gate_json_numbers.gd')
