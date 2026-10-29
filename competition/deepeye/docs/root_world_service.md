# Root world service

`RootWorldService(clock, world_owner, source)` borrows the existing Root objects
after host preparation/claim and original world/source acquisition. It acquires
no process, handle, clock, BOOT, command or action and adds no feedback callback.
The existing source-only diagnostic entry points are unchanged.

The public constructor accepts the exact `QpcHostClock`, the exact retained
production `_RootWorldOwner` with its original native acquisition, and an exact
`CausalSourcePump` in `NEW` or `RUNNING` state. The original initialized current
binding must still be registered and unvetoed. Both callbacks must be the exact
`OwnedWorldField.pose_reader` and `sample_sigma` methods of the same field, whose
executor and scene are those of that original binding. A running source must use
the same clock. These are trusted-process identity conventions, not an OS
security boundary; DTOs, IDs, labels and software fixtures supply no authority.

The read-only `clock` and `source` properties return the original objects.
`deadline_ns` returns the original absolute native containment cap. Reading these
properties performs no polling or clock sampling and never renews the cap.

`poll()` validates the original references and current state, explicitly calls
the original `world_owner.poll()` once, and revalidates before returning its
state. Replacement of a binding, epoch, field, scene, clock or native owner is
refused. Errors, foreign-thread calls and reentry permanently fail this helper;
the original business exception propagates unchanged. It never retries, closes,
kills or retires the source. Root's existing `finally` retains cleanup ownership.

After Root retires the source, it may explicitly call
`poll_retired_source()` to observe the same world's terminal STOP/edit status.
This path requires the original source to be exactly `RETIRED` and repeats all
owner/binding/clock/field checks. It cannot revive a failed helper, accept a fresh
source, sample, write requests or authorize fresh work. Ordinary `poll()` still
refuses a retired source. Root chooses the explicit drain path in its existing
cleanup sequence; this helper adds no lifecycle framework.

The private software seam returns a different exact type and refuses real Root
owners and original native acquisitions. Focused controls exercise the real
source/field identity checks with software external owners and clocks, without
starting an engine, sampling the field, or invoking a QPC factory. A future public
driver must require exact `RootWorldService`; these software controls do not prove
production native acquisition or the physical functional chain.

The H01–H15 contract remains
`c229834bfc2292f5fe4411fc9f12c68487008f9d1adaf31f0144ee7a98173804`.
This helper does not establish FORCE8, ADC, BOOT, motion permission, physical
calibration, the 1%/100 ms gates, H12, G03, R03 or all29 acceptance.
