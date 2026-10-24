extends RefCounted
## Geometry policy shared by editor and private layout codec.
## Inputs mean their exact finite binary64 values, matching Python Gate.
## Coordinates are bounded before arithmetic. Limbs store nonnegative integers
## in units of 2^-1074, so subtraction and squared-distance comparison are exact.
## Base 2^15 bounds every multiply/add/carry intermediate below 2^30.
## For |coordinate| <= 14.85, differences need at most 72 limbs and squared
## distances at most 144. No epsilon, sqrt, float subtraction or normalization.
const EDGE_LIMIT := 14.85
const BASE := 32768
const MASK := 32767
const LIMB_BITS := 15

static func valid_coordinate(value: float) -> bool:
	return is_finite(value) and absf(value) <= EDGE_LIMIT

static func circles_overlap(au: float, av: float, bu: float, bv: float) -> bool:
	# Invalid coordinates fail closed; callers also report the edge/finite reason.
	if not (valid_coordinate(au) and valid_coordinate(av) and valid_coordinate(bu) and valid_coordinate(bv)):
		return true
	var du := _difference_magnitude(au, bu)
	var dv := _difference_magnitude(av, bv)
	var diameter := _magnitude(0.30)
	return _compare(_add(_multiply(du, du), _multiply(dv, dv)), _multiply(diameter, diameter)) < 0

static func _magnitude(value: float) -> Array[int]:
	var bytes := PackedByteArray()
	bytes.resize(8)
	bytes.encode_double(0, value)
	var high: int = bytes.decode_u32(4)
	var exponent: int = (high >> 20) & 2047
	var significand: int = ((high & 1048575) << 32) | bytes.decode_u32(0)
	if exponent != 0:
		significand |= 1 << 52
	if significand == 0:
		return []
	# Normal exponent E has scale 2^(E-1) in units of 2^-1074;
	# subnormals already use those units directly.
	var shift: int = maxi(exponent - 1, 0)
	var result: Array[int] = []
	result.resize(shift / LIMB_BITS)
	result.fill(0)
	var carry: int = 0
	while significand != 0:
		var part: int = ((significand & MASK) << (shift % LIMB_BITS)) | carry
		result.append(part & MASK)
		carry = part >> LIMB_BITS
		significand >>= LIMB_BITS
	if carry != 0:
		result.append(carry)
	return result

static func _difference_magnitude(a: float, b: float) -> Array[int]:
	var x := _magnitude(a)
	var y := _magnitude(b)
	if (a < 0.0) != (b < 0.0):
		return _add(x, y)
	return _subtract(x, y) if _compare(x, y) >= 0 else _subtract(y, x)

static func _compare(a: Array[int], b: Array[int]) -> int:
	if a.size() != b.size():
		return 1 if a.size() > b.size() else -1
	for i in range(a.size() - 1, -1, -1):
		if a[i] != b[i]:
			return 1 if a[i] > b[i] else -1
	return 0

static func _trim(value: Array[int]) -> Array[int]:
	while not value.is_empty() and value.back() == 0:
		value.pop_back()
	return value

static func _add(a: Array[int], b: Array[int]) -> Array[int]:
	var result: Array[int] = []
	var carry: int = 0
	for i in maxi(a.size(), b.size()):
		var part: int = carry + (a[i] if i < a.size() else 0) + (b[i] if i < b.size() else 0)
		result.append(part & MASK)
		carry = part >> LIMB_BITS
	if carry != 0:
		result.append(carry)
	return result

static func _subtract(a: Array[int], b: Array[int]) -> Array[int]:
	# Precondition a >= b.
	var result: Array[int] = []
	var borrow: int = 0
	for i in a.size():
		var part: int = a[i] - (b[i] if i < b.size() else 0) - borrow
		borrow = 1 if part < 0 else 0
		result.append(part + BASE if part < 0 else part)
	return _trim(result)

static func _multiply(a: Array[int], b: Array[int]) -> Array[int]:
	if a.is_empty() or b.is_empty():
		return []
	var result: Array[int] = []
	result.resize(a.size() + b.size())
	result.fill(0)
	for i in a.size():
		if a[i] == 0:
			continue
		var carry: int = 0
		for j in b.size():
			var part: int = result[i + j] + a[i] * b[j] + carry
			result[i + j] = part & MASK
			carry = part >> LIMB_BITS
		result[i + b.size()] = carry
	return _trim(result)

static func _small_product(a: Array[int], multiplier: int, extra: int = 0) -> Array[int]:
	var result: Array[int] = []
	var carry: int = extra
	for digit in a:
		var part: int = digit * multiplier + carry
		result.append(part & MASK)
		carry = part >> LIMB_BITS
	while carry != 0:
		result.append(carry & MASK)
		carry >>= LIMB_BITS
	return _trim(result)

static func _float_bits(value: float) -> int:
	var bytes := PackedByteArray(); bytes.resize(8); bytes.encode_double(0, value)
	return bytes.decode_u64(0)

static func _from_bits(value: int, negative: bool = false) -> float:
	var bytes := PackedByteArray(); bytes.resize(8); bytes.encode_u64(0, value)
	if negative:
		bytes.encode_u32(4, bytes.decode_u32(4) | 2147483648)
	return bytes.decode_double(0)

static func _decimal_compare(target: Array[int], denominator: Array[int], bits: int) -> int:
	return _compare(target, _multiply(_magnitude(_from_bits(bits)), denominator))

static func _digit_at(token: String, index: int) -> bool:
	return index < token.length() and token.unicode_at(index) >= 48 and token.unicode_at(index) <= 57

static func _valid_decimal_token(token: String) -> bool:
	var index: int = 1 if token.begins_with("-") else 0
	if not _digit_at(token, index): return false
	if token[index] == "0": index += 1
	else:
		while _digit_at(token, index): index += 1
	if index < token.length() and token[index] == ".":
		index += 1
		if not _digit_at(token, index): return false
		while _digit_at(token, index): index += 1
	if index < token.length() and token[index] in ["e","E"]:
		index += 1
		if index < token.length() and token[index] in ["-","+"]: index += 1
		if not _digit_at(token, index): return false
		while _digit_at(token, index): index += 1
	return index == token.length()

static func read_decimal(token: String) -> Dictionary:
	# Only called with a JSON numeric token already accepted by the JSON parser.
	# Limit lexical work independently of numeric value. Normal saved binary64
	# tokens are <=25 characters. Long unsupported tokens are explicitly rejected.
	if token.is_empty() or token.length() > 2048:
		return {"ok":false,"reason":"门坐标数字词元超过2048字符上限"}
	if not _valid_decimal_token(token): return {"ok":false,"reason":"门坐标数字词元不是 JSON 数值"}
	var negative: bool = token.begins_with("-")
	var text: String = token.substr(1) if negative else token
	var exponent: int = 0
	var e_index: int = text.to_lower().find("e")
	if e_index >= 0:
		var e_text: String = text.substr(e_index + 1)
		var e_negative: bool = e_text.begins_with("-")
		if e_text.begins_with("-") or e_text.begins_with("+"):
			e_text = e_text.substr(1)
		for ch in e_text:
			exponent = mini(10000, exponent * 10 + ch.unicode_at(0) - 48)
		if e_negative: exponent = -exponent
		text = text.substr(0, e_index)
	var dot: int = text.find(".")
	if dot >= 0:
		exponent -= text.length() - dot - 1
		text = text.replace(".", "")
	var leading: int = 0
	while leading < text.length() and text[leading] == "0": leading += 1
	text = text.substr(leading)
	if text.is_empty(): return {"ok":true,"value":_from_bits(0, negative)}
	var order: int = text.length() + exponent
	if order > 2: return {"ok":false,"reason":"门坐标超出有限几何范围"}
	if order < -324: return {"ok":true,"value":_from_bits(0, negative)}
	var numerator: Array[int] = []
	for ch in text: numerator = _small_product(numerator, 10, ch.unicode_at(0) - 48)
	var denominator: Array[int] = [1]
	for i in absi(exponent):
		if exponent > 0: numerator = _small_product(numerator, 10)
		else: denominator = _small_product(denominator, 10)
	var target := _multiply(_magnitude(1.0), numerator)
	var upper: int = _float_bits(16.0)
	if _decimal_compare(target, denominator, upper) >= 0:
		return {"ok":false,"reason":"门坐标超出有限几何范围"}
	var approximation: float = absf(token.to_float())
	var floor_bits: int = _float_bits(approximation) if is_finite(approximation) and approximation < 16.0 else upper
	var found: bool = false
	for attempt in 4:
		var relation: int = _decimal_compare(target, denominator, floor_bits)
		if relation == 0: return {"ok":true,"value":_from_bits(floor_bits, negative)}
		if relation < 0:
			floor_bits -= 1
		elif _decimal_compare(target, denominator, floor_bits + 1) < 0:
			found = true
			break
		else:
			floor_bits += 1
	if not found:
		var low: int = 0
		var high: int = upper
		while high - low > 1:
			var mid: int = low + ((high - low) >> 1)
			if _decimal_compare(target, denominator, mid) >= 0: low = mid
			else: high = mid
		floor_bits = low
	var midpoint := _add(_magnitude(_from_bits(floor_bits)), _magnitude(_from_bits(floor_bits + 1)))
	var side: int = _compare(_small_product(target, 2), _multiply(midpoint, denominator))
	var rounded: int = floor_bits + 1 if side > 0 or (side == 0 and (floor_bits & 1) != 0) else floor_bits
	return {"ok":true,"value":_from_bits(rounded, negative)}
