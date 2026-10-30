"""Original-session post-transition source sampling; no authority grant."""
from .provider import ProjectionSession
from .._actor_source_custody import _Transition

_STEP = 10_000_000
_MAX = (1 << 63) - 1

def _not_before(origin, completion):
    if (type(origin) is not int or type(completion) is not int
            or not 0 <= origin <= completion <= _MAX):
        raise ValueError('bounded original transition time required')
    result = origin + ((completion-origin + _STEP-1)//_STEP)*_STEP
    if result > _MAX:
        raise ValueError('original source grid overflow')
    return result

def poll_after_finished_transition(session, transition):
    """Return (original payload, original token), or None until a real slot exists.

    Caller releases the completed sample after use. No waiting or replay.
    """
    if type(session) is not ProjectionSession or type(transition) is not _Transition:
        raise ValueError('exact original session and transition required')
    session._check()
    book = session._book
    source = session._link.source
    custody = book._actor_custody
    if (source._source_book is not book or not source._completed_enabled
            or source.state != 'RUNNING' or source._polling
            or custody.pending is not None or transition.custody is not custody
            or not custody.transitions or custody.transitions[-1] is not transition
            or transition.closed is not True or transition.record.get('state') != 'COMPLETE'
            or not any(entry[0] is transition and entry[1] is book._root
                       for entry in session._producer._actions)):
        raise ValueError('observed latest completed original transition required')
    target = _not_before(source._origin, transition.record.get('completion_observed_qpc_ns'))
    now = source._clock()
    if type(now) is not int or not source._high <= now <= _MAX:
        raise ValueError('original clock regressed')
    if now < target:
        return None
    payload = source.poll()
    if payload is None:
        return None
    return payload, source.claim_completed_sample(payload)
