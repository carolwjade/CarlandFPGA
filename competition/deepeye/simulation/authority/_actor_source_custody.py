"""Original-link-only source lineage. No channel, BOOT or movement grant.

All intervals are actual QPC observations. Transition gaps remain gaps; a
post-return observation never becomes C30's exact action.at timestamp.
"""
import threading
from . import motion_executor as motion

_KEY = object()
MAX_TRANSITIONS = 2048


def _nonspatial_lineage(before, after, kind, boot, raw=None):
    """Structural consistency only; the fixed live caller supplies custody."""
    if (type(before) is not motion._Root or type(after) is not motion._Root
            or after.pose is not before.pose or after.pose_revision != before.pose_revision
            or after.frame is not before.frame or after.phase is not before.phase
            or after.executed_until_ns != before.executed_until_ns
            or before.world_invalid or after.world_invalid
            or before.trial_failed or after.trial_failed):
        raise ValueError('nonspatial transition changed numerical pose/history')
    if kind == 'BOOT':
        if (before.boot is not None or after.boot is not boot or after.command is not None
                or after.revision != before.revision+1
                or after.revoke_generation != before.revoke_generation+1
                or after.stopped is not False):
            raise ValueError('original single BOOT lineage required')
    elif kind == 'COMMAND':
        if (before.boot is not boot or after.boot is not boot
                or before.stopped or after.stopped
                or after.revoke_generation != before.revoke_generation
                or type(raw) is not bytes or type(after.command) is not motion._Command
                or after.command.boot is not boot or after.command.raw != raw):
            raise ValueError('original non-STOP admitted command required')
        if after is before:
            if before.command is None or before.command.raw != raw:
                raise ValueError('only the exact original duplicate may keep Root')
        elif (after.revision != before.revision+1 or after.command is before.command
                or (before.command is not None
                    and after.command.sequence <= before.command.sequence)):
            raise ValueError('original command successor required')
    else:
        raise ValueError('fixed nonspatial transition kind required')


class _Transition:
    def __init__(self, key, custody, composition, kind, before, lower, old_span):
        if key is not _KEY:
            raise ValueError('fixed original transition issue path required')
        self.custody, self.composition, self.kind = custody, composition, kind
        self.before, self.lower = before, lower
        self.closed = False
        self.record = dict(kind=kind, state='RESERVED', before_root_revision=before.revision,
            from_pose_revision=before.pose_revision, lower_observed_qpc_ns=lower,
            old_pose_span=old_span,
            completion_observed_qpc_ns=None, exact_commit_qpc_ns=None)


class _ActorSourceCustody:
    def __init__(self, key, link, book):
        if key is not _KEY:
            raise ValueError('original link custody issue path required')
        self.link, self.book = link, book
        self.pending = None
        self.transitions, self.closed_spans = [], []

    def _context(self, transition=None):
        from .original_world_actor_link import _OriginalWorldActorLink
        link, book = self.link, self.book
        if (type(link) is not _OriginalWorldActorLink or link.book is not book
                or book._actor_custody is not self or book._source is not link.source
                or book._owner is not link.owner or book._binding is not link.binding
                or threading.get_ident() != link.thread):
            raise ValueError('original actor/source custody changed')
        # Ordinary book checks also run INSIDE its original EM scope/source
        # poll. The action-only _registered gate intentionally excludes those.
        # The book checks native/field/epoch custody immediately after this.
        if (link.owner._actor_link is not link
                or link.owner._actor_links.get(id(link)) is not link
                or link.service._owner is not link.owner
                or link.service._source is not book._source
                or link.service._failed or link.binding.executor is not link.executor
                or link.source._pose_reader is not link.pose_reader
                or link.source._sampler is not link.sampler
                or link.source._profile is not link.profile):
            raise ValueError('original singleton actor/source association changed')
        if transition is None:
            if self.pending is not None:
                raise ValueError('source is excluded during original actor transition')
        elif (type(transition) is not _Transition or transition is not self.pending
                or transition.custody is not self or transition.closed
                or transition.composition is not link.composition
                or not link.claimed):
            raise ValueError('exact pending original transition required')
        if transition is not None:
            link._registered()

    def _root_check(self, root, transition):
        self._context(transition)
        if transition is None:
            if root is not self.book._root:
                raise ValueError('unrecorded actor Root successor')
        elif transition.before is not self.book._root:
            raise ValueError('original transition predecessor changed')

    def reserve(self, composition, kind):
        book, link = self.book, self.link
        self._context()
        if (kind not in ('BOOT', 'COMMAND', 'STEP') or not link.claimed
                or link.composition is not composition or composition._world_action_link is not link
                or composition._executor is not link.executor or not composition._busy
                or composition._retired or book._busy or book._active is not None
                or link.source._polling or link.owner._em_scope_active is not None
                or len(self.transitions) >= MAX_TRANSITIONS):
            raise ValueError('idle original source and genuine serialized actor required')
        book._poll()
        link._registered()
        old_end = book._time()
        span = book._span(old_end)
        lower = book._time()  # A separate real observation, never old_end+1.
        book._check()
        if lower <= old_end:
            raise ValueError('old pose span must end before actual transition lower bound')
        transition = _Transition(_KEY, self, composition, kind, book._root, lower, span)
        self.closed_spans.append(span)
        self.transitions.append(transition)
        self.pending = transition  # Retained before any actor Root effect.
        return transition

    def _accept(self, transition, after, completion):
        book = self.book
        transition.record.update(state='COMPLETE', after_root_revision=after.revision,
            to_pose_revision=after.pose_revision, completion_observed_qpc_ns=completion)
        book._root, book._base_pose = after, after.pose
        book._pose_values = (tuple(after.pose.position_m), tuple(after.pose.orientation_xyzw))
        book._span_from = book._span_through = completion
        transition.closed = True
        self.pending = None

    def finish_nonspatial(self, transition):
        book, link, actor = self.book, self.link, transition.composition
        book._check(_actor_transition=transition)
        if (not actor._busy or actor._retired or actor._state != 'ACTIVE'
                or actor._runtime._latched or actor._runtime._boot is not actor._boot
                or actor._executor_activation is not actor._boot
                or actor._runtime_activation is not actor._boot):
            raise ValueError('whole original actor activation/admission must complete')
        raw = None
        if transition.kind == 'COMMAND':
            tx = actor._input_transaction
            if (tx is None or tx.request_raw is None or actor._command_record is None
                    or actor._command_record.raw != tx.request_raw
                    or actor._runtime._command is None
                    or actor._runtime._command.raw != tx.request_raw):
                raise ValueError('original complete command transaction required')
            raw = tx.request_raw
        after = link.executor._root
        _nonspatial_lineage(transition.before, after, transition.kind, actor._boot, raw)
        completion = book._time()
        actor._progress.observe_time(completion)
        book._check(_actor_transition=transition)
        if link.executor._root is not after:
            raise ValueError('actor Root changed after completion observation')
        self._accept(transition, after, completion)

    def finish_step(self, slot):
        book, link = self.book, self.link
        transition = getattr(slot, 'book_transition', None)
        self._context(transition)
        actor = link.composition
        if (transition is None or transition.kind != 'STEP' or link.slot is not slot
                or slot.uncertainty is not None or not slot.committed
                or slot.receipt is None or not slot.getter_admitted
                or actor._busy or actor._retired or actor._runtime._stepping
                or actor._runtime._latched or link.executor._root is not slot.post_root
                or actor._runtime._executed_until_ns != slot.receipt.end_ns
                or slot.post_root.executed_until_ns != slot.receipt.end_ns):
            raise ValueError('original admitted numerical step closure required')
        book._check(_actor_transition=transition)
        completion = book._time()
        if (completion < slot.receipt.end_ns or completion >= slot.deadline_ns
                or slot.post_cas_observed_qpc_ns > completion):
            raise ValueError('actual completion must follow elapsed numerical interval')
        book._check(_actor_transition=transition)
        transition.record.update(pre_cas_qpc_ns=slot.pre_cas_qpc_ns,
            post_cas_observed_qpc_ns=slot.post_cas_observed_qpc_ns,
            model_executed_until_qpc_ns=slot.receipt.end_ns,
            publication_operation_id=slot.publication.operation_id,
            getter_readback_qpc_ns=slot.publication.readback_ns)
        self._accept(transition, slot.post_root, completion)
        return completion

    def abort(self, transition, reason):
        if transition is not None and transition is self.pending:
            transition.record.update(state='FAILED', reason=reason[:128])
            root = self.link.executor._root
            if type(root) is motion._Root:
                transition.record['failed_observed_root_revision'] = root.revision
                transition.record['failed_observed_pose_revision'] = root.pose_revision
            slot = self.link.slot
            if slot is not None and getattr(slot, 'book_transition', None) is transition:
                transition.record['effect_observation'] = slot.effect_observation
                transition.record['returned_receipt_observed'] = slot.receipt is not None
        self.book.fail(reason)

    def evidence(self):
        return dict(kind='original_actor_pose_revision_intervals_v1',
            transitions=[t.record for t in self.transitions], closed_spans=self.closed_spans,
            pending=self.pending.record if self.pending is not None else None,
            exact_action_time='unavailable;only_original_observation_intervals',
            native_interval_atomic=False)


def _issue_original_actor_book(link):
    from .original_world_actor_link import _OriginalWorldActorLink
    from .root_source_book import RootSourceBook
    if (type(link) is not _OriginalWorldActorLink or link.claimed
            or link.composition is not None or link.book is not None
            or link.source.state != 'NEW' or link.source._source_book is not None
            or link.source._em_scope_factory is None):
        raise ValueError('one fresh original source/link with scoped EM required')
    link._registered()
    book = RootSourceBook(link.owner, link.binding, link.field, link.source,
                          scoped_em_receipts=True)
    custody = _ActorSourceCustody(_KEY, link, book)
    book._actor_custody, link.book = custody, book
    custody._context()
    return book
