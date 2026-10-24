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
		var carry: int = 0
		for j in b.size():
			var part: int = result[i + j] + a[i] * b[j] + carry
			result[i + j] = part & MASK
			carry = part >> LIMB_BITS
		result[i + b.size()] = carry
	return _trim(result)
