"""Pure TRACE sample comparison and byte accounting; never board authority.

The caller retains original bytes and independently establishes provenance.  The
existing B131 bundle/codec is required. No action, transport or clock is opened.
"""
import binascii
import struct
import sys
from . import functional50_b131_loader as loader

_SAMPLE_KEYS=frozenset(('channel','index','tick_ms','source_tick_ms','value','valid','saturated','held','source_fault'))
_META_KEYS=frozenset(('session','config_epoch','e','first_sequence'))
_MAX_ITEMS=4096
_MAX_ATTACHMENT=8*1024*1024


def _require(condition, message):
    if not condition:raise ValueError(message)


def _int(value, low, high, name):
    _require(type(value) is int and low<=value<=high, name+' must be a bounded exact integer')
    return value


def _snapshot_sample(item, private):
    _require(type(item) is dict and all(type(k) is str for k in item) and set(item)==_SAMPLE_KEYS,'exact sample fields required')
    out=dict(item)
    _int(out['channel'],0,3,'channel');_int(out['index'],0,0xffffffff,'index')
    _int(out['tick_ms'],0,0xffffffff if private else 0xffffffffffffffff,'tick')
    for key in ('valid','saturated','held','source_fault'):_require(type(out[key]) is bool,key+' must be exact bool')
    if out['valid']:
        _int(out['value'],0,4095 if private else 65535,'sample value')
        _int(out['source_tick_ms'],0,0xffffffff if private else 0xffffffffffffffff,'source tick')
        _require((out['source_tick_ms']<out['tick_ms']) if out['held'] else (out['source_tick_ms']==out['tick_ms']),'declared source tick inconsistent')
    else:
        _require(out['value'] is None and out['source_tick_ms'] is None and not out['held'] and not out['saturated'],'invalid sample shape')
    return out


def _private_frame(frame,binding,codec):
    _require(type(frame) is bytes and 35<=len(frame)<=46,'bounded private frame required')
    magic,version,kind,length,epoch,sequence,tick=struct.unpack_from('<2sBBBBHI',frame,0)
    _require(magic==b'\xa5\x5a' and version==3 and kind==0xe4 and 21<=length<=32 and len(frame)==length+14,'unknown private frame layout')
    _require(epoch==binding['config_epoch'],'private epoch mismatch')
    _require(struct.unpack_from('<H',frame,len(frame)-2)[0]==binascii.crc_hqx(frame[2:-2],0xffff),'private CRC mismatch')
    payload=frame[12:-2];_require(payload[0]==2,'private payload revision mismatch')
    record=codec.decode_payload(bytes([1])+payload[1:],binding)
    _require(record['count']==1 and record['first_tick_ms']<=0xffffffff and tick==record['first_tick_ms'],'B94 singleton/tick required')
    point=record['points'][0]
    _require(not point['valid'] or point['value']<=4095,'B94 uint12 count required')
    record['sequence']=sequence;record['config_epoch']=epoch
    return record


def inspect_capture(original_samples, received_frames, *, metadata, layout, bundle, companions=(), transport_capture=None):
    """Compare supplied sample facts with original frames, not their authenticity.

    tick_ms is the codec field name: interpreted as microseconds ONLY for the
    explicit private 1us layout, otherwise milliseconds. `transport_capture`
    counts exactly supplied bytes and is not asserted to be a complete upload.
    """
    _require(type(bundle) is loader._Bundle and sys.modules.get('adapter128') is bundle.adapter
             and sys.modules.get('_adapter128_trace_codec') is bundle.adapter.codec,'fixed B131 codec bundle required')
    codec=bundle.adapter.codec
    _require(type(layout) is str and layout in ('candidate_abi3_type7_v1','trace94_private_1us_v2'),'unsupported layout')
    private=layout=='trace94_private_1us_v2'
    _require(type(metadata) is dict and all(type(k) is str for k in metadata) and set(metadata)==_META_KEYS,'exact declared metadata required')
    meta=dict(metadata);_int(meta['session'],0,0xffffffff,'session');_int(meta['config_epoch'],0,255,'epoch');_int(meta['first_sequence'],0,65535,'first sequence')
    _require(type(meta['e']) is int and meta['e'] in (0,1,2,4,8),'unsupported declared E')
    _require(not private or meta['e']==0,'B94 selected profile requires E=0')
    _require(type(original_samples) in (tuple,list) and 0<len(original_samples)<=_MAX_ITEMS,'bounded original samples required')
    _require(type(received_frames) in (tuple,list) and 0<len(received_frames)<=_MAX_ITEMS and all(type(f) is bytes for f in received_frames),'bounded original frame bytes required')
    _require(type(companions) in (tuple,list) and len(companions)<=4 and all(type(v) is bytes for v in companions) and sum(map(len,companions))<=_MAX_ATTACHMENT,'bounded companion bytes required')
    _require(transport_capture is None or (type(transport_capture) is bytes and len(transport_capture)<=_MAX_ATTACHMENT),'bounded transport capture required')
    samples=[_snapshot_sample(x,private) for x in original_samples];frames=tuple(received_frames)
    _require(meta['first_sequence']+len(frames)-1<=65535,'sequence wrap unsupported')
    binding=dict(session=meta['session'],config_epoch=meta['config_epoch'],e=meta['e'])
    decoded=[];blocks=[];last_by_channel={};code_bytes=payload_bytes=frame_bytes=0
    for i,frame in enumerate(frames):
        record=_private_frame(frame,binding,codec) if private else codec.decode_frame(frame,binding)
        _require(record['sequence']==meta['first_sequence']+i,'frame sequence mismatch')
        channel=record['channel'];ledger=record['ledger'];code_bytes+=ledger['stored_code_bytes'];payload_bytes+=ledger['payload_bytes'];frame_bytes+=len(frame)
        blocks.append(dict(channel=channel,sequence=record['sequence'],mode=record['mode'],e=record['e'],count=record['count'],code_bytes=ledger['stored_code_bytes'],payload_bytes=ledger['payload_bytes'],frame_bytes=len(frame)))
        for point in record['points']:
            candidate=dict(channel=channel,**point);last=last_by_channel.get(channel)
            _require(last is None or (candidate['index']>last[0] and candidate['tick_ms']>last[1]),'channel index/time order mismatch')
            last_by_channel[channel]=(candidate['index'],candidate['tick_ms']);decoded.append(candidate)
            _require(len(decoded)<=_MAX_ITEMS,'decoded sample budget exceeded')
    _require(len(decoded)==len(samples),'missing or extra sample')
    points=[];errors=[]
    for original,actual in zip(samples,decoded):
        for key in ('channel','index','tick_ms','source_tick_ms','valid','saturated','held','source_fault'):
            _require(original[key]==actual[key],'source or sample '+key+' mismatch')
        difference=None if not original['valid'] else actual['value']-original['value']
        if difference is not None:errors.append(abs(difference))
        points.append(dict(channel=original['channel'],index=original['index'],tick=original['tick_ms'],source_tick=original['source_tick_ms'],valid=original['valid'],raw=original['value'],reconstructed=actual['value'],difference=difference))
    baseline=2*len(errors);overhead=frame_bytes-payload_bytes
    return dict(layout=layout,time_unit='us' if private else 'ms',declared_metadata=meta,
                source_authentication='NOT_EVALUATED',board_verified=False,authority='NOT_EVALUATED',
                frames=blocks,points=points,exact_match=(all(v==0 for v in errors) if errors else None),
                max_abs_error=max(errors) if errors else None,within_declared_e=(all(v<=meta['e'] for v in errors) if errors else None),
                bytes=dict(baseline_u16=baseline,code=code_bytes,payload=payload_bytes,frame_overhead=overhead,frame_wire=frame_bytes,
                           companion_supplied=sum(map(len,companions)),captured_upload=None if transport_capture is None else len(transport_capture),upload_total=None),
                ratios=dict(code_to_baseline=(code_bytes/baseline if baseline else None),frame_to_baseline=(frame_bytes/baseline if baseline else None)),
                accounting_note='companion bytes are supplied only; transport capture completeness and board origin are not evaluated')
