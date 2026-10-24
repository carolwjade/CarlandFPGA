"""Build reviewable framing vectors independently of integration/wire.py."""
import binascii
import json
from pathlib import Path
import struct

PRODUCT = Path(__file__).resolve().parents[1]


def frame(type_id, payload, epoch=2, sequence=0x1234, tick=0x12345678):
    body = bytes([3, type_id, len(payload), epoch]) + struct.pack('<HI', sequence, tick) + payload
    return b'\xa5\x5a' + body + struct.pack('<H', binascii.crc_hqx(body, 0xffff))


def main():
    interface = json.loads((PRODUCT / 'docs/interface.json').read_bytes())
    valid = []
    for name, spec in interface['frames'].items():
        payload = bytearray(spec['payload_bytes'])
        for field in spec['fields']:
            size, start = field['bytes'], field['payload_offset']
            if field['type'] == 'i16': value = (-57).to_bytes(2, 'little', signed=True)
            else: value = bytes((i + 1) & 255 for i in range(size))
            payload[start:start + size] = value
        raw = frame(spec['type'], payload)
        valid.append(dict(name=name, type_id=spec['type'], config_epoch=2,
            sequence=0x1234, tick_ms=0x12345678, payload_hex=payload.hex(),
            frame_hex=raw.hex(), legacy_diagnostic=spec['type'] in (3, 4)))
    good = frame(8, bytes(18))
    invalid = [dict(name='truncated_crc', frame_hex=good[:-1].hex()),
               dict(name='trailing_byte', frame_hex=(good + b'\0').hex()),
               dict(name='unknown_type', frame_hex=frame(0x77, b'').hex()),
               dict(name='wrong_STATE_payload_length', frame_hex=frame(8, bytes(17)).hex()),
               dict(name='unfrozen_TRACE', frame_hex=frame(7, bytes(32)).hex())]
    for pos in range(2, len(good)):
        bad = bytearray(good); bad[pos] ^= 1
        invalid.append(dict(name='bit_corruption_%02d' % pos, frame_hex=bad.hex()))
    doc = dict(schema=1, evidence_scope='A independent framing and quantized-motion software vectors; no peer or hardware acceptance',
        requirements_sha256=interface['immutable_scope_sha256'], valid_frames=valid,
        invalid_frames=invalid, motion_vectors=[
            dict(profile='stress_300', yaw_q=y, pitch_q=p, speed_code=s, accepted=ok)
            for y,p,s,ok in [(57,0,20,True),(58,0,20,False),(40,40,20,True),
                             (41,41,20,False),(1,0,0,False),(0,0,0,True)]])
    path = PRODUCT / 'tests/vectors/abi3_reference.json'; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(dict(path=str(path), valid=len(valid), invalid=len(invalid))))


if __name__ == '__main__': main()
