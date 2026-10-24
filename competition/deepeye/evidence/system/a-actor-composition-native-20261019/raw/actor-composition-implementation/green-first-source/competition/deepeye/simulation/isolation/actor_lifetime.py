"""Internal original-acquisition observation, never PID discovery/adoption.

A positive result is a recent nonsignaled sample, not guaranteed future life,
responsive inference, authentication, or meaningful AI. No provider is registered.
"""
from ..authority.pc_direct_runtime import AiLease


def _reference(owner):
    owner._checkpoint()
    if owner._state not in ('RUNNING_UNBOUND', 'BOUND_ACTIVE'):
        raise ValueError('running original actor required')
    reference = owner._process
    if (owner._cleanup_attempted or owner._resources._sealed or
            reference is not owner._original_process or reference is None or
            not owner._resources.owns(reference) or reference.native != owner._original_native or
            reference.kind != 'process' or reference.release != 'kernel' or
            reference.attempted or reference.ambiguous or reference.terminal_confirmed):
        raise ValueError('original acquisition continuity lost')
    return reference


def _sample(owner, now_ns=None):
    from .actor_owner import _integer
    reference = _reference(owner)
    epoch = owner._epoch
    before = owner._time()
    if now_ns is not None and _integer(now_ns) > before:
        raise ValueError('runtime time exceeds trusted current clock')
    if _reference(owner) is not reference:
        raise ValueError('original reference changed before observation')
    state = owner._api.Wait(owner._original_native, 0)
    owner._checkpoint(epoch)
    if type(state) is not int or state != 258:
        if type(state) is int and state == 0: reference.terminal_confirmed = True
        raise ValueError('original process terminal or life observation unknown')
    after = owner._time()
    if after - before >= owner._policy.max_probe_ns:
        raise ValueError('life observation exceeded explicit probe budget')
    deadline = min(before + owner._policy.sample_age_cap_ns, owner._run_deadline)
    if after >= deadline or (owner._state == 'RUNNING_UNBOUND' and after >= owner._ready_deadline):
        raise ValueError('fixed actor/readiness/sample deadline expired')
    owner._checkpoint(epoch)
    if _reference(owner) is not reference:
        raise ValueError('original reference changed during observation')
    return deadline


def _observe(owner, boot, now_ns):
    from .actor_owner import _integer
    _integer(now_ns)
    if owner._state != 'BOUND_ACTIVE' or boot is not owner._boot:
        raise ValueError('exact active trusted BOOT binding required')
    deadline = _sample(owner, now_ns)
    return AiLease(owner._boot, owner.instance_id, deadline)


__all__ = []
