"""Author relaxed fingers and thumb opposition, without moving either grip root."""
import argparse
from pathlib import Path

import numpy as np

import verify_hands as hand
from build_weapon import encode_glb

SOURCES = Path(__file__).resolve().parent / "grip-refinement/finger-surface/joint-loops"
RELAX = {"Thumb": .18, "Index": .18, "Mid": .30, "Ring": .42, "Pinky": .54}
THUMB_LANDMARKS_MM = ((39, 5.5, -40.5), (14, 31.5, -45), (-16, 30, -42))
SOURCE_DIGESTS = {
    "right_hand_joint.glb": "199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64",
    "left_hand_joint.glb": "0295c147673a5cf15b4265cbfcb83391d2fa399b8be778c54ecc789fc61c46f7",
}


def unit(vector):
    return vector / np.linalg.norm(vector)


def multiply(first, second):
    xyz = first[3] * second[:3] + second[3] * first[:3] + np.cross(first[:3], second[:3])
    return unit(np.r_[xyz, first[3] * second[3] - first[:3] @ second[:3]])


def tip_vertices(document, binary, digit):
    prim = document["meshes"][0]["primitives"][0]
    attr = prim["attributes"]
    joints = np.array(document["skins"][0]["joints"])[hand.values(document, binary, attr["JOINTS_0"])]
    weights = hand.values(document, binary, attr["WEIGHTS_0"])
    dominant = joints[np.arange(len(joints)), weights.argmax(axis=1)]
    worlds = hand.sampled_worlds(document, binary, "grip", 0)
    nodes = {node["name"]: index for index, node in enumerate(document["nodes"])}
    second, third = (nodes[digit + str(joint)] for joint in (2, 3))
    distal_axis = unit((worlds[third] - worlds[second])[:3, 3])
    eligible = np.flatnonzero(dominant == third)
    projection = hand.skin(document, binary, prim, worlds)[eligible] @ distal_axis
    return eligible[projection >= np.quantile(projection, .82)]


def write_key(document, binary, accessor_id, index, quat):
    accessor = document["accessors"][accessor_id]
    view = document["bufferViews"][accessor["bufferView"]]
    assert accessor["type"] == "VEC4" and accessor["componentType"] == 5126
    assert accessor["count"] == 2 and view.get("byteStride", 16) == 16
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + 16 * index
    binary[offset:offset + 16] = np.asarray(quat, dtype="<f4").tobytes()


def build(src, dest, side):
    if src.name in SOURCE_DIGESTS and hand.digest(src) != SOURCE_DIGESTS[src.name]:
        raise ValueError(f"Unexpected starting hand: {src.name}")
    document, data = hand.read(src)
    binary = bytearray(data)
    animation, = document["animations"]
    nodes = {node["name"]: index for index, node in enumerate(document["nodes"])}
    outputs = {channel["target"]["node"]: animation["samplers"][channel["sampler"]]["output"]
               for channel in animation["channels"]}
    assert len(outputs) == 15
    sign = 1 if side == "R" else -1
    thumb = side + "_Thumb"
    tip = tip_vertices(document, binary, thumb)
    prim = document["meshes"][0]["primitives"][0]
    for digit, amount in RELAX.items():
        for joint in (1, 2, 3):
            accessor = outputs[nodes[f"{side}_{digit}{joint}"]]
            start, end = hand.values(document, binary, accessor).astype(float)
            if start @ end < 0:
                end = -end
            angle = np.arccos(np.clip(unit(start) @ unit(end), -1, 1))
            relaxed = start if angle < 1e-6 else unit(
                np.sin((1 - amount) * angle) * start + np.sin(amount * angle) * end)
            write_key(document, binary, accessor, 0, relaxed)
    for digit, degrees in (("Index", -8.), ("Mid", -4.), ("Ring", 4.), ("Pinky", 8.)):
        node = nodes[f"{side}_{digit}1"]
        worlds = hand.sampled_worlds(document, binary, "grip", 1)
        local_axis = unit(np.linalg.solve(worlds[node][:3, :3], [1., 0., 0.]))
        half_angle = np.radians(degrees) * .5
        delta = np.r_[local_axis * np.sin(half_angle), np.cos(half_angle)]
        accessor = outputs[node]
        fixed = multiply(hand.values(document, binary, accessor)[1], delta)
        write_key(document, binary, accessor, 1, fixed)
        document["nodes"][node]["rotation"] = fixed.tolist()
    for joint, xyz in enumerate(THUMB_LANDMARKS_MM, 1):
        worlds = hand.sampled_worlds(document, binary, "grip", 1)
        node = nodes[thumb + str(joint)]
        transform = worlds[node]
        origin = transform[:3, 3]
        end = (worlds[nodes[thumb + str(joint + 1)]][:3, 3] if joint < 3 else
               hand.skin(document, binary, prim, worlds)[tip].mean(axis=0))
        target = np.array(xyz) * (.001 * np.array([sign, 1, 1]))
        basis = np.linalg.inv(transform[:3, :3])
        old, new = unit(basis @ (end - origin)), unit(basis @ (target - origin))
        delta = unit(np.r_[np.cross(old, new), 1 + old @ new])
        accessor = outputs[node]
        fixed = multiply(hand.values(document, binary, accessor)[1], delta)
        write_key(document, binary, accessor, 1, fixed)
        document["nodes"][node]["rotation"] = fixed.tolist()
    dest.write_bytes(encode_glb(document, binary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--decoded", action="store_true", help="also patch PNG review companions")
    options = parser.parse_args()
    options.output_dir.mkdir(parents=True, exist_ok=True)
    for name, side, folder in (("right", "R", SOURCES), ("left", "L", SOURCES / "left-derivation")):
        for suffix in (("", "_decoded") if options.decoded else ("",)):
            build(folder / f"{name}_hand_joint{suffix}.glb",
                  options.output_dir / f"{name}_hand{suffix}.glb", side)
