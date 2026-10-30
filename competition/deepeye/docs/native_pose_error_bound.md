# Native endpoint affine body error bound

This inactive pure mathematical component does not admit a getter, allocate a margin, prove a receipt, or establish native continuity, rendering, physics, board, or H03 acceptance. Caller must independently establish that the actual global getter corresponds to the retained pose, freeze and operation and that the entire relevant root-space asset is contained in the nominal capsule expanded by the supplied `asset_error` d. Child transform arithmetic and GPU/physics semantics are not covered by this component.

`affine_body_bound(position, quaternion, global_columns, global_origin, half_segment, capsule_radius, pivot_radius, asset_error)` accepts only fixed immutable tuples of exact `Fraction` scalars, with individual numerator and denominator up to 1200 bits. Columns are the three Godot basis columns, each containing three row components. Inputs must be finite values already represented exactly; `decode_ieee` provides exact finite big-endian IEEE 32/64 hexadecimal decoding and identifies positive and negative zero as the same rational. NaN, infinity, malformed tokens, non-exact values, non-tuples, zero quaternion, negative sizes, and a pivot radius below half-segment plus capsule radius are refused. The input bound includes all finite binary64 values, including subnormals. This bound is a computation resource limit, not a physical limit.

The exact rational normalized quaternion formula produces Q. Let t be the numerical root position, g the getter translation and G the getter basis. For each actual asset point p, with nominal capsule C and d such that A is a subset of C plus a Euclidean ball of radius d, `||p|| <= pivot_radius+d` and

```
||(g + G p) - (t + Q p)||
    <= ||g-t|| + ||G-Q||_F * (pivot_radius+d) = E_get.
```

The returned translation and matrix norms are outward dyadic square-root bounds with denominator at most 2^64. `sqrt_enclosure` floors the scaled squared rational with integer division, takes its integer square root, and adds one scaled unit if the root is not exact. Therefore `lower² <= x <= upper²`, and the gap is at most 2^-64; no float square root or floating-point rounding assumption is used. This absolute granularity can be conservative for tiny values. `getter_error` is E_get; `total_error` is E_get+d, because orthogonal Q preserves the already-certified d. Do not add the same asset error again. Other numerical, obstacle, pose, or native-evaluation errors must remain separately accounted for by their own proven budgets.

`fits_cap` tests E_get <= an explicit positive exact Fraction. It is a mathematical comparison only; equality passes, and it does not activate any gate or create a budget. The supplied cap must be incorporated into a separately reviewed new world construction and original full-volume geometry, gate and path certification before any use. Post-effect excess cannot undo an action or establish an earlier native interval. The caller must also account for difference between the affine-set model and the actual child, visual, physics, and rendering operations before making claims about them.
