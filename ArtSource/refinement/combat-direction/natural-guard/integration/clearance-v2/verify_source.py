"""Independent byte-level RAW scope checks and two in-memory rejection fixtures."""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
OLD = REPO / 'ArtSource/refinement/combat-direction/natural-guard/candidate/family-v1/attack_right_raw.glb'
NEW = REPO / 'ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/candidate/attack_right_raw.glb'
ALLOWED = {'L_Upperarm','L_Forearm','L_Hand'}


def decode(data):
    length = struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length]), data[28+length:]


def location(doc,index):
    accessor = doc['accessors'][index]
    view = doc['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset',0)+accessor.get('byteOffset',0)
    width = {'SCALAR':1,'VEC3':3,'VEC4':4}[accessor['type']]
    assert accessor['componentType']==5126 and 'byteStride' not in view
    return start, accessor['count'], width


def verify(before,after):
    a,ab = before
    b,bb = after
    assert a==b,'RAW JSON/rest/accessor/skin/material/time descriptors changed'
    animation = a['animations'][0]
    assert len(animation['channels'])==234
    changed = []
    mutable_ranges = []
    for channel in animation['channels']:
        sampler = animation['samplers'][channel['sampler']]
        name = a['nodes'][channel['target']['node']]['name']
        path = channel['target']['path']
        start,count,width = location(a,sampler['output'])
        size = count*width*4
        av,bv = ab[start:start+size],bb[start:start+size]
        if av!=bv:
            assert name in ALLOWED and path=='rotation',(name,path)
            assert av[:width*4]==bv[:width*4] and av[-width*4:]==bv[-width*4:], 'guard endpoint changed'
            changed.append(name+'/'+path)
            mutable_ranges.append((start,start+size))
        start,count,width = location(a,sampler['input'])
        assert ab[start:start+count*width*4]==bb[start:start+count*width*4], 'time grid changed'
    assert {v.split('/')[0] for v in changed}==ALLOWED
    assert len(ab)==len(bb),'RAW BIN length changed'
    cursor = 0
    for start,end in sorted(mutable_ranges):
        assert ab[cursor:start]==bb[cursor:start], 'non-authorized BIN payload changed'
        cursor=end
    assert ab[cursor:]==bb[cursor:],'non-authorized trailing BIN payload changed'
    return changed


def main():
    old,new = decode(OLD.read_bytes()),decode(NEW.read_bytes())
    changed = verify(old,new)
    rejected = []
    doc, binary = new
    for bone,key in [('R_Hand',60),('L_Upperarm',0)]:
        channel = next(c for c in doc['animations'][0]['channels'] if doc['nodes'][c['target']['node']]['name']==bone and c['target']['path']=='rotation')
        sampler = doc['animations'][0]['samplers'][channel['sampler']]
        start,count,width = location(doc,sampler['output'])
        modified = bytearray(binary)
        value = struct.unpack_from('<f',modified,start+key*width*4)[0]
        struct.pack_into('<f',modified,start+key*width*4,value+.01)
        try:
            verify(old,(doc,bytes(modified)))
        except AssertionError:
            rejected.append(bone+'@'+str(key))
    assert len(rejected)==2
    result = {'passed':True,'original_raw_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),
        'candidate_raw_sha256':hashlib.sha256(NEW.read_bytes()).hexdigest(),
        'changed_tracks':changed,'track_count':234,'all_other_channel_payloads_exact':True,
        'all_234_guard_endpoint_values_exact':True,'all_time_payloads_exact':True,
        'all_raw_JSON_rest_skin_material_descriptors_exact':True,
        'all_BIN_bytes_outside_three_rotation_payloads_exact':True,
        'in_memory_negative_fixtures_rejected':rejected}
    (HERE / 'source_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
