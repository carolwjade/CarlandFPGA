extends SceneTree
const R=preload("res://editor/gate_json_numbers.gd")
const C=preload("res://editor/layout_codec.gd")
const N=preload("res://editor/gate_numeric.gd")
func _initialize() -> void:
	var parts: PackedStringArray=[]
	for i in 95000:parts.append('"x%d":0'%i)
	var text: String='{"decoy":{'+','.join(parts)+'},"layout":{"gates":{"entry":{"u":14.850000000000001}}}}'
	var t: int=Time.get_ticks_usec();var result: Dictionary=C.decode(text)
	print("WIDE_BYTES=",text.to_utf8_buffer().size()," CODEC_US=",Time.get_ticks_usec()-t," REJECTED=",not result.ok)
	var valid: bool=not result.ok and text.to_utf8_buffer().size()<=1048576
	for levels in [31,32,33]:
		var nested: String='{"x":'.repeat(levels)+'0'+'}'.repeat(levels)
		var parsed: Dictionary=JSON.parse_string(nested);t=Time.get_ticks_usec();var restored: Dictionary=R.restore(nested,parsed)
		print("DEPTH=",levels," RESTORE=",restored.ok," US=",Time.get_ticks_usec()-t)
		valid=valid and restored.ok==(levels<=32)
	# Duplicate keys with surrogate-pair spelling, inside an unrelated object.
	var duplicate: String='{"x":{"😀":0,"\\ud83d\\ude00":1}}'
	var parsed: Dictionary=JSON.parse_string(duplicate)
	valid=valid and not R.restore(duplicate,parsed).ok
	# Record approximation error for long supported tokens; exact checks occurred
	# in independent_probe. A bad approximation only selects the fallback path.
	var rows: Array=JSON.parse_string(FileAccess.get_file_as_string("res://tests/independent_decimal.json"))
	for row in rows:
		if row.label in ["maximum-dense-token","maximum-near-midpoint"]:
			var approximate: float=absf(String(row.token).to_float())
			var exact: float=String(row.hex).hex_decode().decode_double(0)
			print("APPROX label=",row.label," finite=",is_finite(approximate)," ulps=",N._float_bits(approximate)-N._float_bits(exact))
	print("RESOURCE_PASS=",valid)
	quit(0 if valid else 1)
