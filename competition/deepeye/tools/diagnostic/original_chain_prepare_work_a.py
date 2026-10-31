"""Fixed detached B131 preparation job; no source, clock, transport or authority."""
import json
import threading
from . import functional50_b131_loader as loader

_KEY=object()

class _PrepareJob:
    """One immutable byte-input job; thread and partial attempt remain retained."""
    def __init__(self,key,bundle,payload_bytes,draft_bytes,facts_bytes,binding_bytes,metadata_bytes,origin,domain,received,evaluated):
        if key is not _KEY or type(bundle) is not loader._Bundle:
            raise ValueError('fixed private preparation job required')
        if not all(type(x) is bytes for x in (payload_bytes,draft_bytes,facts_bytes,binding_bytes,metadata_bytes)):
            raise ValueError('immutable detached inputs required')
        self._bundle=bundle;self._adapter=bundle.adapter;self._reducer=bundle.reducer
        self._inputs=(payload_bytes,draft_bytes,facts_bytes,binding_bytes,metadata_bytes,origin,domain,received,evaluated)
        self.done=threading.Event();self.attempt=None;self.result=None;self.error=None
        self.thread=threading.Thread(target=self._run,daemon=True)
    def start(self,key):
        if key is not _KEY:raise ValueError('private job start required')
        self.thread.start()
    def _run(self):
        try:
            from . import original_source_trace_scan_a as scan
            payload_bytes,draft_bytes,facts_bytes,binding_bytes,metadata_bytes,origin,domain,received,evaluated=self._inputs
            payload,draft,facts,binding,metadata=(json.loads(v.decode('utf8')) for v in (payload_bytes,draft_bytes,facts_bytes,binding_bytes,metadata_bytes))
            if not all(type(x) is dict for x in (payload,draft,facts,binding,metadata)):
                raise ValueError('detached object shape')
            if self._bundle.adapter is not self._adapter or self._bundle.reducer is not self._reducer:
                raise ValueError('fixed B131 modules changed')
            scan._check_bundle(self._bundle)
            self.attempt=scan._construct_bytes(payload,payload_bytes,draft,origin,domain,received,evaluated,facts,'NEW_ORIGINAL_LIVE_ROOT',clock_metadata=metadata)
            request,source,companions=self.attempt
            self.result=self._adapter.prepare_bytes(request,source,companions,build_binding=binding)
            scan._check_bundle(self._bundle)
            if self._bundle.adapter is not self._adapter or self._bundle.reducer is not self._reducer:
                raise ValueError('fixed B131 modules changed during preparation')
        except BaseException as error:self.error=error
        finally:self.done.set()
