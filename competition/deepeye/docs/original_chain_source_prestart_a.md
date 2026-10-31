# Pre-start source pump binding

A pump can be constructed with the actual original v2 scanner explicitly prepared with `defer_start=True`, while the source and Book remain NEW and untouched. Constructor checks the original source, Book, session, QPC and owner identities and empty unstarted state; it does not start anything or choose an origin. Existing already-started construction remains supported.

Root starts the source exactly once, activates the scanner against its actual origin, enables the pump, and immediately calls `poll_once(session)`. Enabling before the actual source and scanner are ready fails closed. Sampling is not guaranteed to occur in the zero slot: the actual QPC and source determine the returned slot, and no slot is invented or filled.

The new tests use synthetic stand-ins only, not the actual hardware or a native world.
