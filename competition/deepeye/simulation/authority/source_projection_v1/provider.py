"""Original Root callsite attachments; no transport or authority grant.

External receipt objects and fields are supplied only at their real Root callsite.
Opaque labels attest object identity locally; they do not authenticate facts.
"""
import threading
import uuid
from . import assembler

_KEY=object()

class ProjectionSession:
    def __init__(self,key,owner,link,book,producer):
        if key is not _KEY: raise ValueError('original factory required')
        self._owner,self._link,self._book,self._producer=owner,link,book,producer
        self._thread=threading.get_ident();self._refs=[];self._current=[];self._registries=[];self._tokens=[]
        for value in (book,link.binding,link,getattr(link,'composition',None)):
            if value is not None:self._bind(value)

    @classmethod
    def attach_original(cls,owner,link,book):
        producer=assembler.attach_original(owner,link,book)
        return cls(_KEY,owner,link,book,producer)

    def _check(self):
        if threading.get_ident()!=self._thread:raise ValueError('original session thread required')
        self._producer._check()

    def _bind(self,ref):
        if ref is None:raise ValueError('missing object is not a receipt')
        for existing,label in self._refs:
            if existing is ref:return label
        label='root-'+uuid.uuid4().hex
        self._producer.bind_id(ref,label)
        self._refs.append((ref,label))
        return label

    def bind_observed(self,original_ref):
        """Bind a genuine object observed by trusted Root at its callsite.

        Caller owns provenance; this method does not turn it into evidence.
        """
        self._check();return self._bind(original_ref)

    def observe_config(self,original_ref,fields):
        self._check();self._bind(original_ref);self._producer.attach_config(original_ref,fields)

    def observe_admission(self,original_ref,fields):
        self._check();self._bind(original_ref);self._producer.attach_admission(original_ref,fields)

    def observe_capture(self,original_ref,sample_token,*,candidate,fields):
        self._check()
        sample=getattr(sample_token,'_draft',None)
        if (getattr(sample_token,'_book',None) is not self._book
                or getattr(sample_token,'_ended',None) is not True
                or not any(sample is item for item in self._book._samples)):
            raise ValueError('actual completed retained sample token required')
        self._bind(original_ref)
        self._producer.attach_capture(original_ref,sample,candidate=candidate,fields=fields)
        self._tokens.append(sample_token)  # Retain the original token as well as its draft.

    def observe_finished_transition(self,transition,*,successor_root,slot=None,fields):
        self._check();custody=self._book._actor_custody
        if (custody.pending is not None or not any(transition is item for item in custody.transitions)
                or transition.closed is not True or successor_root is not self._book._root
                or successor_root is not self._link.executor._root):
            raise ValueError('actual completed original transition required')
        if transition.kind=='STEP':
            if (slot is None or not any(slot is item for item in self._owner._commits)
                    or getattr(slot,'book_transition',None) is not transition
                    or getattr(slot,'committed',None) is not True
                    or getattr(slot,'uncertainty',None) is not None
                    or getattr(slot,'receipt',None) is None
                    or getattr(slot,'post_root',None) is not successor_root
                    or getattr(getattr(slot,'original_witness',None),'link',None) is not self._link):
                raise ValueError('actual successful retained step required')
        elif slot is not None:raise ValueError('nonspatial transition has no slot')
        self._bind(transition)
        if slot is not None:
            self._bind(slot)
            witness=slot.original_witness
            if witness is not None:
                self._bind(witness)
                if witness.allocated_receipt is not None:self._bind(witness.allocated_receipt)
            self._bind(slot.receipt)
            if slot.publication is not None:
                self._bind(slot.publication)
                if slot.publication.admitted_readback is not None:self._bind(slot.publication.admitted_readback)
                policy=self._link.binding.world_values.budget_derivation
                if policy is not None:self._bind(policy)
        else:
            if successor_root.boot is not None:self._bind(successor_root.boot)
            if successor_root.command is not None:self._bind(successor_root.command)
        self._producer.attach_transition(transition,successor_root=successor_root,slot=slot,fields=fields)

    def read_current(self):
        self._check();current=self._producer.read_current()
        self._bind(current)
        if current.get('valid_span') is not None:self._bind(current['valid_span'])
        self._current.append(current);return current

    def attach_registry(self,original_view,context,generation,*,as_of_qpc_ns,observation_ref):
        """Explicit real Root registry observation; never infer as_of from getter.

        Caller must supply its original registry view and an independently
        retained observation/hold receipt supporting the named time. C42 and
        downstream C36 still validate correspondence.
        """
        self._check()
        if original_view is None or observation_ref is None or type(as_of_qpc_ns) is not int or as_of_qpc_ns<0:
            raise ValueError('original registry observation and time required')
        self._bind(original_view);self._bind(observation_ref)
        self._producer.attach_registry(original_view,context,generation,as_of_qpc_ns=as_of_qpc_ns)
        self._registries.append((original_view,observation_ref,as_of_qpc_ns))

    def export(self,*,current_read,registry_ref,candidate_ref,history_refs=(),enabled=False):
        self._check()
        if not any(current_read is item for item in self._current):raise ValueError('original current read required')
        return self._producer.export(current_read=current_read,registry_ref=registry_ref,
            candidate_ref=candidate_ref,history_refs=history_refs,enabled=enabled)
