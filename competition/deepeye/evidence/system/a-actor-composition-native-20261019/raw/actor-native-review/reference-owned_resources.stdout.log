"""In-memory acquisition ledger. Never reconstruct an OS target from a PID."""
from dataclasses import dataclass
from .resource_cleanup import CleanupCoordinator, ErrorInfo, Outcome, Resource


class OwnedReleaseError(RuntimeError):
    pass


@dataclass(eq=False)
class OwnedReference:
    resource_id: str
    label: str
    native: object
    release: str
    kind: str
    profile_id: str | None
    recovery: bool = False
    attempted: bool = False
    outcome: Outcome | None = None
    terminal_confirmed: bool = False
    keepalive: object = None
    ambiguous: bool = False


def error_info(stage, error, resource_id=None):
    try:
        message = str(error)
    except BaseException:
        message = '<exception text unavailable>'
    return ErrorInfo(stage, resource_id, type(error).__name__, message)


class OwnedResources:
    """One launcher/one cleanup attempt. Keep this object alive if unresolved.

    Numeric values can be reused only after a confirmed release of the previous
    acquisition instance. A release that threw or returned unknown is never
    automatically issued again, including by the final coordinator.
    """
    def __init__(self, provenance):
        self.provenance = provenance
        self._references = []
        self._releaser = None
        self._sealed = False
        self._coordinator = None
        self.cleanup_result = None
        self.profile = None
        self.profile_path = None
        self.errors = []

    @property
    def references(self):
        return tuple(self._references)

    @property
    def unresolved(self):
        return tuple(ref for ref in self._references if ref.outcome is not Outcome.CONFIRMED)

    def owns(self, ref):
        return any(ref is item for item in self._references)

    def bind_releaser(self, callback):
        if self._releaser is not None or not callable(callback):
            raise ValueError('one explicit release backend required')
        self._releaser = callback

    def own_handle(self, label, value, *, release='kernel', kind='handle', recovery=False,
                   profile_dependent=True, keepalive=None):
        ref, error = self._record_handle(label, value, release=release, kind=kind, recovery=recovery,
                                         profile_dependent=profile_dependent, keepalive=keepalive)
        if error is not None:
            raise error
        return ref

    def _record_handle(self, label, value, *, release='kernel', kind='handle', recovery=False,
                       profile_dependent=True, keepalive=None):
        if self._sealed:
            raise RuntimeError('acquisition after cleanup was sealed')
        value = getattr(value, 'value', value)
        if value is None or value == 0:
            raise ValueError('cannot own an absent native reference')
        domain = 'kernel' if release == 'kernel' else release
        conflict = None
        for prior in self._references:
            if prior.release == domain and prior.native == value and prior.outcome is not Outcome.CONFIRMED:
                if not prior.attempted:
                    raise ValueError('native reference already owned')
                conflict = prior
        ref = OwnedReference(f'{label}:{len(self._references) + 1}', label, value, domain, kind,
                             self.profile.resource_id if self.profile and profile_dependent else None, recovery)
        self._references.append(ref)
        ref.keepalive = keepalive
        if conflict is not None:
            # Keep the new acquisition even when an earlier close's lost reply
            # makes the reused numeric binding ambiguous. Neither record may be
            # acted on automatically until exact ownership is reconciled.
            conflict.ambiguous = ref.ambiguous = True
            ref.attempted, ref.outcome = True, Outcome.UNKNOWN
            self.errors.append(ErrorInfo('acquisition', ref.resource_id, 'AmbiguousReuse',
                                         'native value reused after unconfirmed release'))
            return ref, ValueError('new acquisition retained with ambiguous native reuse')
        return ref, None

    def _record_pair(self, first, second):
        """Record both results of one successful acquisition before raising.

        Each item is (label, native value, registration options). No OS action,
        reporting callback or release is performed. In-memory allocation failure
        itself retains the existing Python-level limitation.
        """
        refs, errors, unexpected = [], [], []
        for label, value, options in (first, second):
            try:
                ref, error = self._record_handle(label, value, **options)
            except BaseException as error:
                refs.append(None)
                errors.append(error)
                unexpected.append(error)
            else:
                refs.append(ref)
                if error is not None:
                    errors.append(error)
        # Formatting a secondary diagnostic must also wait until both records
        # have been attempted. Ambiguities already carry their ledger errors.
        self.errors.extend(error_info('paired_registration', error) for error in unexpected)
        return tuple(refs), errors

    def own_pair(self, first, second):
        refs, errors = self._record_pair(first, second)
        if errors:
            raise errors[0]
        return refs

    def own_profile(self, name, sid):
        if self.profile is not None:
            raise ValueError('one newly created profile per owner')
        refs, errors = self._record_pair(
            ('profile', name, {'release': 'profile', 'kind': 'profile', 'profile_dependent': False}),
            ('profile_sid', sid, {'release': 'sid', 'profile_dependent': False}))
        self.profile = refs[0]
        if self.profile is not None and refs[1] is not None:
            refs[1].profile_id = self.profile.resource_id
        if errors:
            raise errors[0]
        return self.profile

    def set_profile_path(self, path):
        if self._sealed or self.profile is None or path is None or not str(path):
            raise ValueError('known path from the owned profile required before cleanup')
        self.profile_path = path

    def own_process(self, pi):
        # No inspection, formatting or reporting between successful CreateProcess
        # and registering BOTH returned handles. Memory allocation failure itself
        # remains outside this Python-level atomicity guarantee.
        return self.own_pair(('process', pi.hProcess, {'kind': 'process'}),
                             ('primary_thread', pi.hThread, {'recovery': True}))

    def find(self, label):
        return next(ref for ref in reversed(self._references) if ref.label == label)

    def release_once(self, ref):
        if not self.owns(ref):
            raise ValueError('foreign ownership reference')
        if ref.attempted:
            return ref.outcome
        if self._releaser is None:
            raise ValueError('release backend not bound')
        ref.attempted, ref.outcome = True, Outcome.UNKNOWN
        try:
            value = self._releaser(ref)
            if type(value) is not Outcome:
                raise TypeError('release backend returned an unclassified result')
            ref.outcome = value
            if value is not Outcome.CONFIRMED:
                self.errors.append(ErrorInfo('release', ref.resource_id, 'UnconfirmedOutcome', value.value))
        except BaseException as error:
            self.errors.append(error_info('release', error, ref.resource_id))
        return ref.outcome

    def release_checked(self, ref, *, preserve_primary=False):
        outcome = self.release_once(ref)
        if outcome is not Outcome.CONFIRMED and not preserve_primary:
            raise OwnedReleaseError('release unconfirmed: ' + ref.resource_id)
        return outcome

    def cleanup(self, backend, report_sink, primary_error=None):
        if self._sealed:
            raise RuntimeError('owner cleanup already attempted; reconcile without replay')
        self._sealed = True
        processes = tuple(ref.resource_id for ref in self._references if ref.kind == 'process')
        plan = tuple(Resource(ref.resource_id, self.provenance.owner_id, ref.kind, ref,
                              ref.profile_id, processes if ref.recovery else ()) for ref in self._references)
        self._coordinator = CleanupCoordinator(self.provenance, plan, backend, report_sink)
        self.cleanup_result = self._coordinator.cleanup(primary_error)
        return self.cleanup_result

    def summary(self):
        return [{'resource_id': ref.resource_id, 'label': ref.label, 'release': ref.release,
                 'native': ref.native if isinstance(ref.native, (int, str)) else '<held object>',
                 'attempted': ref.attempted, 'outcome': None if ref.outcome is None else ref.outcome.value,
                 'terminal_confirmed': ref.terminal_confirmed,
                 'ambiguous': ref.ambiguous} for ref in self._references]
