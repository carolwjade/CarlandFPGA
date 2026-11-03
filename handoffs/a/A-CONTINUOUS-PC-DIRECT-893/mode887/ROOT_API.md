887 is a distinct mode-selection-only candidate derived from exact frozen884
controller884.py SHA c1a81c06638086e30e1f896b0861a380fc45e838464e70d9f239b2b90e34d9a1.
Original884 controller/delivery/manifest/patch/API are restored/unchanged bytes.
The temporary mode candidate formed after Root clarification is preserved here;
no runtime effects occurred. Adopt887 separately if reviewed; no old operation
is replayed. W884 client files remain frozen at their delivered exact hashes.

cfg.admission_mode is an INITIAL UI preference. Once actual frozen.json exists,
selected_mode(cfg,frozen) adopts its strict BOARD_PWM/PC_DIRECT choice. Missing
mode in old frozen files defaults BOARD_PWM. Optional cfg.required_admission_mode
can constrain a particular Root commissioning run; foreign/mismatching values
refuse before NativeClient connect/board start. The selected mode/direct bool and
public result/status fields are determined only after this fresh frozen choice.
After nativebind mode remains immutable. No source/AI/PWM/clock/TTL/law/control
changes. Four protected847/884 functions have identical ASTs. New pure mode seam
checks UI choice overrides config preference, legacy missing default, required
match, foreign frozen, required mismatch and foreign required. No full old control
suite was repeated for this one seam; no network/UI/board/native/model/source run.

All other API/behavior is exactly884 ROOT_API.md. Requirements revision2 canonical
SHA2afd4515da6f03dad47d453fb3692c5f67fa2fb09084665d425de1340648bf4d.
Formal all29/quality/dual-H12 remain not_run. Root owns actual integration/run.
