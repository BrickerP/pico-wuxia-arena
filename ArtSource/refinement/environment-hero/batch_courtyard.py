"""Build the localized draw-batch variant of the shipped, static courtyard GLB."""
import argparse
import copy
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

SOURCE_SHA = "beb91140ee4f7b2f6090daba64626ebb3280cb0b1d586a47a4c063dce7ff8fef"
REGIONS = {
    "FacadeWest": ("Facade_GroundWindow_Existing", "Facade_GroundWindow_-4.62",
                   "Facade_UpperWindow_-4.55", "Facade_UpperWindow_-2.3"),
    "FacadeEast": ("Facade_GroundWindow_2.47", "Facade_GroundWindow_4.62",
                   "Facade_UpperWindow_2.3", "Facade_UpperWindow_4.55"),
    "FacadeEntry": ("Facade_UpperWindow_0", "EH_OneWindow_NativeEntrance_Geometry"),
    "TavernRoof": ("EH_TavernMainRoof", "EH_TavernMainRoof_Rafters", "EH_TavernPorchRoof",
                   "EH_TavernPorchRoof_Rafters", "Facade_TileEndRow"),
    "TavernFacade": ("EH_TavernTimber", "EH_TavernWalls", "EH_S2_TimberJointFaces", "Facade_WallInfills"),
    "DistantWest": ("EH_TownLowerEave_1", "EH_TownRoof_1"),
    "DistantEast": ("EH_TownLowerEave_2", "EH_TownRoof_2"),
    "SideGalleryTrim": ("EH_SideGalleryTimber", "EH_SideGalleryWindows"),
}
DTYPES = {5123: "<u2", 5125: "<u4", 5126: "<f4"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read(path):
    source = path.read_bytes()
    assert source[:4] == b"glTF" and struct.unpack_from("<II", source, 4) == (2, len(source))
    end = 20 + struct.unpack_from("<I", source, 12)[0]
    assert source[16:20] == b"JSON" and source[end+4:end+8] == b"BIN\0"
    return json.loads(source[20:end]), memoryview(source)[end+8:]


def view(bank, index):
    item = bank[0]["bufferViews"][index]
    start = item.get("byteOffset", 0)
    return bank[1][start:start + item["byteLength"]]


def data(bank, index):
    spec = bank[0]["accessors"][index]
    width = WIDTHS[spec["type"]]
    dtype = np.dtype(DTYPES[spec["componentType"]])
    assert not spec.get("sparse") and not spec.get("normalized")
    stride = bank[0]["bufferViews"][spec["bufferView"]].get("byteStride", width * dtype.itemsize)
    return np.ndarray((spec["count"], width), dtype, view(bank, spec["bufferView"]),
                      offset=spec.get("byteOffset", 0), strides=(stride, dtype.itemsize))


def origins(doc):
    offsets = {}
    def visit(index, offset, translated):
        assert index not in offsets
        node = doc["nodes"][index]
        translated = translated and not ({"matrix", "rotation", "scale"} & node.keys())
        position = offset + np.array(node.get("translation", (0., 0., 0.)))
        offsets[index] = (position, translated)
        for child in node.get("children", []):
            visit(child, position, translated)
    for root in doc["scenes"][doc["scene"]]["nodes"]:
        visit(root, np.zeros(3), True)
    return offsets


def write_glb(path, doc, binary):
    packed = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode()
    packed += b" " * (-len(packed) % 4)
    binary += b"\0" * (-len(binary) % 4)
    path.write_bytes(struct.pack("<4sIII4s", b"glTF", 2, 28 + len(packed) + len(binary), len(packed), b"JSON") +
                     packed + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def build(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError("Use a separate candidate path")
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Source is not the reviewed courtyard")
    bank = read(source)
    doc = bank[0]
    dest = copy.deepcopy(doc)
    for name in ("accessors", "bufferViews", "meshes"):
        dest[name] = []
    removed = defaultdict(set)
    offsets = origins(doc)
    blob = bytearray()
    old_views, old_attrs, old_meshes = {}, {}, {}
    def put_view(raw, spec):
        blob.extend(b"\0" * (-len(blob) % 4))
        index = len(dest["bufferViews"])
        dest["bufferViews"].append(dict(spec, buffer=0, byteOffset=len(blob), byteLength=len(raw)))
        blob.extend(raw)
        return index
    def copy_view(index):
        if index not in old_views:
            old_views[index] = put_view(view(bank, index), doc["bufferViews"][index])
        return old_views[index]
    def copy_accessor(index):
        if index not in old_attrs:
            spec = doc["accessors"][index]
            old_attrs[index] = len(dest["accessors"])
            dest["accessors"].append(dict(spec, bufferView=copy_view(spec["bufferView"])))
        return old_attrs[index]
    def new_accessor(values, component_type, shape, target, bounds=False):
        values = np.asarray(values, dtype=DTYPES[component_type])
        rec = dict(bufferView=put_view(values.tobytes(), {"target": target}), count=len(values),
                   type=shape, componentType=component_type)
        if bounds:
            rec.update(min=values.min(axis=0).tolist(), max=values.max(axis=0).tolist())
        dest["accessors"].append(rec)
        return len(dest["accessors"]) - 1

    for image in dest["images"]:
        image["bufferView"] = copy_view(image["bufferView"])
    parent, = dest["scenes"][dest["scene"]]["nodes"]
    assert np.array_equal(offsets[parent][0], np.zeros(3)) and offsets[parent][1]
    names = {node["name"]: i for i, node in enumerate(doc["nodes"])}
    summary = {}
    for region, members in REGIONS.items():
        buckets = defaultdict(list)
        for name in members:
            node_idx = names[name]
            assert offsets[node_idx][1]
            mesh = doc["meshes"][doc["nodes"][node_idx]["mesh"]]
            for index, prim in enumerate(mesh["primitives"]):
                assert prim.keys() <= {"material","attributes","indices","mode"} and prim.get("mode",4) == 4
                assert doc["materials"][prim["material"]].get("alphaMode","OPAQUE") == "OPAQUE"
                key = (prim["material"], tuple(sorted(prim["attributes"])))
                buckets[key].append((node_idx,index,prim))
        primitives = []
        savings = 0
        for (material, layout), parts in buckets.items():
            if len(parts) < 2:
                continue
            streams = defaultdict(list)
            indices = []
            count = 0
            for node_idx, index, prim in parts:
                removed[node_idx].add(index)
                for attr in layout:
                    src = data(bank, prim["attributes"][attr])
                    assert src.dtype == np.dtype("<f4")
                    streams[attr].append((src + offsets[node_idx][0]).astype("<f4") if attr == "POSITION" else src)
                indices.append(data(bank,prim["indices"]).ravel().astype(np.uint32) + count)
                count += len(streams["POSITION"][-1])
            attrs = {name:new_accessor(np.concatenate(pieces), 5126, "VEC" + str(pieces[0].shape[1]), 34962,
                                       name == "POSITION") for name,pieces in streams.items()}
            new_index = new_accessor(np.concatenate(indices), 5123 if count <= 65535 else 5125,"SCALAR",34963)
            primitives.append(dict(attributes=attrs, indices=new_index, material=material))
            savings += len(parts) - 1
        if primitives:
            dest["nodes"][parent]["children"].append(len(dest["nodes"]))
            dest["nodes"].append({"name":"Batch_"+region, "mesh":len(dest["meshes"])})
            dest["meshes"].append({"name":"Batch_"+region, "primitives":primitives})
        summary[region] = savings

    for i, node in enumerate(doc["nodes"]):
        if "mesh" not in node:
            continue
        mesh_id = node["mesh"]
        mesh = doc["meshes"][mesh_id]
        keep = tuple(j for j in range(len(mesh["primitives"])) if j not in removed[i])
        if not keep:
            del dest["nodes"][i]["mesh"]
            continue
        key = mesh_id, keep
        if key not in old_meshes:
            prims = []
            for j in keep:
                prim = mesh["primitives"][j]
                prims.append(dict(prim, indices=copy_accessor(prim["indices"]), attributes={
                    k:copy_accessor(v) for k,v in prim["attributes"].items()}))
            old_meshes[key] = len(dest["meshes"])
            dest["meshes"].append(dict(mesh, primitives=prims))
        dest["nodes"][i]["mesh"] = old_meshes[key]
    dest["buffers"] = [{"byteLength":len(blob)}]
    write_glb(destination, dest, blob)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.destination), indent=2))
