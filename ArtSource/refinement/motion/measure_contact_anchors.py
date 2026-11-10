"""Read runtime glTF bone anchors at the slash times used by EnemyAnimator.

This exports source animation measurements. It does not modify the GLB or
change gameplay contact geometry. Run from the repository root with Python 3.
"""

from __future__ import annotations

import bisect
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "app/src/main/assets/models/opponents/base.glb"
OUTPUT = Path(__file__).with_name("slash_contact_anchors.json")
BONES = ("BoneRoot", "Hip", "Waist", "Spine02", "Head")
TIMES = (1.55, 1.85, 2.067, 2.117, 2.167, 2.6, 3.4)
PROXIES = {
    "head": ("Head", [0.0, 1.62, 0.0]),
    "body_top": ("Spine02", [0.0, 1.40, 0.0]),
    "body_bottom": ("Hip", [0.0, 0.55, 0.0]),
}


def identity():
    return [[float(row == column) for column in range(4)] for row in range(4)]


def multiply(a, b):
    return [[sum(a[row][k] * b[k][column] for k in range(4))
             for column in range(4)] for row in range(4)]


def inverse(a):
    rows = [list(a[row]) + identity()[row] for row in range(4)]
    for column in range(4):
        pivot = max(range(column, 4), key=lambda row: abs(rows[row][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        if abs(scale) < 1e-15:
            raise ValueError("singular root matrix")
        rows[column] = [value / scale for value in rows[column]]
        for row in range(4):
            if row != column:
                factor = rows[row][column]
                rows[row] = [x - factor * y for x, y in zip(rows[row], rows[column])]
    return [row[4:] for row in rows]


def normalize(q):
    length = math.sqrt(sum(value * value for value in q))
    if not math.isfinite(length) or length <= 0:
        raise ValueError("invalid source quaternion")
    return [value / length for value in q]


def slerp(a, b, fraction):
    a, b = normalize(a), normalize(b)
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-value for value in b], -dot
    dot = min(1.0, dot)
    if dot > 0.999999:
        return normalize([x + (y - x) * fraction for x, y in zip(a, b)])
    angle = math.acos(dot)
    denominator = math.sin(angle)
    a_weight = math.sin((1 - fraction) * angle) / denominator
    b_weight = math.sin(fraction * angle) / denominator
    return normalize([x * a_weight + y * b_weight for x, y in zip(a, b)])


def trs(translation, rotation, scale):
    x, y, z, w = normalize(rotation)
    matrix = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    for row in range(3):
        for column in range(3):
            matrix[row][column] *= scale[column]
        matrix[row][3] = translation[row]
    return matrix


def transform_point(matrix, point):
    return [sum(matrix[row][column] * point[column] for column in range(3)) + matrix[row][3]
            for row in range(3)]


def from_column_major(values):
    return [[values[row + column * 4] for column in range(4)] for row in range(4)]


def measure(source):
    data = source.read_bytes()
    magic, version, declared_length = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or declared_length != len(data):
        raise ValueError("expected GLB 2.0")
    chunks = {}
    offset = 12
    while offset < len(data):
        size, kind = struct.unpack_from("<II", data, offset)
        chunks[kind] = data[offset + 8:offset + 8 + size]
        offset += 8 + size
    doc = json.loads(chunks[0x4E4F534A])
    binary = chunks[0x004E4942]
    nodes = doc["nodes"]
    names = {node["name"]: i for i, node in enumerate(nodes) if "name" in node}
    parents = {child: i for i, node in enumerate(nodes) for child in node.get("children", [])}
    root_index = names["TripoWarrior_Root"]
    accessor_cache = {}

    def accessor(index):
        if index in accessor_cache:
            return accessor_cache[index]
        item = doc["accessors"][index]
        if item["componentType"] != 5126 or "sparse" in item:
            raise ValueError("animation channels must use dense Float accessors")
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[item["type"]]
        view = doc["bufferViews"][item["bufferView"]]
        if view.get("buffer", 0) != 0:
            raise ValueError("unexpected external animation buffer")
        stride = view.get("byteStride", width * 4)
        start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
        values = [struct.unpack_from("<" + "f" * width, binary, start + i * stride)
                  for i in range(item["count"])]
        accessor_cache[index] = values
        return values

    animations = {animation["name"]: animation for animation in doc["animations"]}

    def pose(clip, seconds):
        overrides = {}
        if clip is not None:
            for channel in animations[clip]["channels"]:
                target = channel["target"]
                path = target["path"]
                if path not in ("translation", "rotation", "scale"):
                    raise ValueError("unsupported animation path " + path)
                sampler = animations[clip]["samplers"][channel["sampler"]]
                times = [value[0] for value in accessor(sampler["input"])]
                values = accessor(sampler["output"])
                right = bisect.bisect_right(times, seconds)
                if right == 0:
                    value = values[0]
                elif right == len(times):
                    value = values[-1]
                elif sampler.get("interpolation", "LINEAR") == "STEP":
                    value = values[right - 1]
                elif sampler.get("interpolation", "LINEAR") == "LINEAR":
                    left = right - 1
                    fraction = (seconds - times[left]) / (times[right] - times[left])
                    value = slerp(values[left], values[right], fraction) if path == "rotation" else [
                        a + (b - a) * fraction for a, b in zip(values[left], values[right])
                    ]
                else:
                    raise ValueError("unsupported animation interpolation")
                overrides[(target["node"], path)] = value
        worlds = {}

        def world(index):
            if index in worlds:
                return worlds[index]
            node = nodes[index]
            if "matrix" in node:
                if any(key[0] == index for key in overrides):
                    raise ValueError("animated matrix node")
                values = node["matrix"]
                local = [[values[row + column * 4] for column in range(4)] for row in range(4)]
            else:
                local = trs(
                    overrides.get((index, "translation"), node.get("translation", [0, 0, 0])),
                    overrides.get((index, "rotation"), node.get("rotation", [0, 0, 0, 1])),
                    overrides.get((index, "scale"), node.get("scale", [1, 1, 1])),
                )
            worlds[index] = multiply(world(parents[index]), local) if index in parents else local
            return worlds[index]

        root_inverse = inverse(world(root_index))
        result = {}
        for name in BONES:
            matrix = multiply(root_inverse, world(names[name]))
            result[name] = {
                "node_index": names[name],
                "position_metres": [matrix[row][3] for row in range(3)],
                "matrix_column_major": [matrix[row][column] for column in range(4) for row in range(4)],
            }
        return result

    rest = pose(None, 0)
    idle = pose("idle", 0)
    calibration = pose("idle", 1.0)
    proxy_local = {
        role: transform_point(inverse(from_column_major(calibration[bone]["matrix_column_major"])), point)
        for role, (bone, point) in PROXIES.items()
    }
    samples = []
    for seconds in TIMES:
        anchors = pose("slash", seconds)
        for name, anchor in anchors.items():
            point = anchor["position_metres"]
            anchor["delta_from_default_rest_metres"] = [a - b for a, b in zip(point, rest[name]["position_metres"])]
            anchor["delta_from_idle_zero_metres"] = [a - b for a, b in zip(point, idle[name]["position_metres"])]
        proxies = {}
        for role, (bone, legacy_point) in PROXIES.items():
            point = transform_point(from_column_major(anchors[bone]["matrix_column_major"]), proxy_local[role])
            proxies[role] = {
                "owner_bone": bone,
                "root_position_metres": point,
                "delta_from_legacy_proxy_metres": [a - b for a, b in zip(point, legacy_point)],
            }
        samples.append({"clip": "slash", "source_seconds": seconds, "anchors": anchors, "calibrated_proxies": proxies})

    output = {
        "schema": "wuxia.source-contact-anchor-measurement/v1",
        "measured_on": "2026-11-10",
        "source": str(source.relative_to(ROOT)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "frame": {"relative_to": "TripoWarrior_Root", "units": "metres", "up": "+Y", "prepared_forward": "+Z"},
        "evaluation": "glTF node T*R*S through complete parent chain; LINEAR vector interpolation, shortest-arc quaternion slerp, STEP channels; matrix expressed relative to character root",
        "references": {"default_rest": rest, "idle_at_source_seconds_zero": idle,
                       "idle_at_source_seconds_one": calibration},
        "proxy_calibration": {
            "clip": "idle", "source_seconds": 1.0,
            "formula": "localPoint = inverse(ownerMatrixAtIdleOne) * legacyProxyPoint; currentPoint = ownerMatrixAtSlashTime * localPoint",
            "local_points_metres": proxy_local,
            "legacy_points_metres": {role: point for role, (_, point) in PROXIES.items()},
            "unchanged_radii_metres": {"head": 0.16, "body": 0.24},
        },
        "samples": samples,
        "limits": [
            "Bone origins are anchors, not skin surface or hitbox centres.",
            "Source evaluation does not prove the SDK's runtime joint transform or crossfade output.",
            "Seven key poses do not bound the entire slash trajectory.",
            "Proxy calibration preserves the legacy idle@1.0 centres; it does not prove those centres fit the rendered skin.",
            "No gameplay thresholds, capsule radii, state timings or three-round rules were changed.",
        ],
    }
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", choices=("base", "indigo", "veteran"))
    args = parser.parse_args()
    reports = []
    for actor in ((args.actor,) if args.actor else ("base", "indigo", "veteran")):
        report = measure(SOURCE.with_name(actor + ".glb"))
        report["actor"] = actor
        reports.append(report)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    base_report = next((report for report in reports if report["actor"] == "base"), None)
    if base_report is not None:
        OUTPUT.write_text(json.dumps(base_report, indent=2, ensure_ascii=False) + "\n")
    profile_path = OUTPUT.with_name("proxy_alignment_profiles.json")
    profile = {
        "schema": "wuxia.calibrated-proxy-keyposes/v1",
        "measured_on": "2026-11-10",
        "coordinate_frame": reports[0]["frame"],
        "calibration": reports[0]["proxy_calibration"]["formula"],
        "actors": [{
            "actor": report["actor"], "source": report["source"], "sha256": report["sha256"],
            "calibration": report["proxy_calibration"],
            "keyposes": [{"source_seconds": sample["source_seconds"],
                          "proxies": sample["calibrated_proxies"]} for sample in report["samples"]],
        } for report in reports],
        "limits": reports[0]["limits"],
    }
    if args.actor:
        existing = json.loads(profile_path.read_text())
        replacement = profile["actors"][0]
        if not any(actor["actor"] == args.actor for actor in existing["actors"]):
            raise ValueError("selected actor has no existing profile")
        existing["actors"] = [replacement if actor["actor"] == args.actor else actor
                              for actor in existing["actors"]]
        profile = existing
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n")
    print("Saved", OUTPUT.relative_to(ROOT), "and", profile_path.relative_to(ROOT))
    for report in reports:
        print(report["actor"], report["sha256"])
        for sample in report["samples"]:
            print(sample["source_seconds"], {role: [round(x, 6) for x in values["delta_from_legacy_proxy_metres"]]
                                             for role, values in sample["calibrated_proxies"].items()})


if __name__ == "__main__":
    main()
