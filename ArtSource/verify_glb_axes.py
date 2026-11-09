"""Check candidate GLB native coordinates and basic glTF structure.

Run with Python 3 from any directory. This is a file-level check, not a PICO
runtime/device test. PICO Stage uses +X right, +Y up and +Z toward the user.
"""

import copy
import json
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_glb(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<III", data)
    length, kind = struct.unpack_from("<II", data, 12)
    if magic != 0x46546C67 or version != 2 or total != len(data) or kind != 0x4E4F534A:
        raise ValueError("invalid GLB header: " + str(path))
    doc = json.loads(data[20:20+length])
    if doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("not glTF 2.0: " + str(path))
    if doc.get("extensionsRequired"):
        raise ValueError("unreviewed required GLB extensions: " + str(path))
    return doc


def check_points(doc, root_name, expected):
    nodes = doc["nodes"]
    by_name = {}
    for index, node in enumerate(nodes):
        name = node.get("name")
        if name in expected or name == root_name:
            if name in by_name:
                raise ValueError("duplicate node: " + name)
            by_name[name] = (index, node)
    missing = ({root_name} | set(expected)) - set(by_name)
    if missing:
        raise ValueError("missing nodes: " + ", ".join(sorted(missing)))
    root = by_name[root_name][1]
    if root.get("matrix") or root.get("translation", [0,0,0]) != [0,0,0] or \
       root.get("rotation", [0,0,0,1]) != [0,0,0,1] or root.get("scale", [1,1,1]) != [1,1,1]:
        raise ValueError(root_name + " is not an identity root")
    for name, point in expected.items():
        index, node = by_name[name]
        if index not in root.get("children", []):
            raise ValueError(name + " is not a direct child of " + root_name)
        actual = node.get("translation", [0,0,0])
        if any(abs(a-b) > .0005 for a,b in zip(actual, point)):
            raise ValueError("native GLB coordinate mismatch for " + name + ": " + str(actual))


dao = load_glb(HERE / "dao" / "dao_study.glb")
dao_points = {"Grip": (0,-.114,0), "Blade_Base": (.022,.015,0),
              "Blade_Tip": (.0532,.735,0)}
check_points(dao, "DAO_Root", dao_points)
print("PASS dao: Y-up native GLB grip and blade anchors")

tavern = load_glb(HERE / "tavern" / "tavern_slice.glb")
tavern_points = {"Door_Left_Root": (-.925,0,0), "Door_Right_Root": (.925,0,0),
                 "Lantern_Root": (-1.43,2.865,.42)}
check_points(tavern, "Tavern_Root", tavern_points)
# The lantern is on the entrance's +Z side, the side facing the user.
broken = copy.deepcopy(tavern)
next(node for node in broken["nodes"] if node.get("name") == "Lantern_Root")["translation"][2] *= -1
try:
    check_points(broken, "Tavern_Root", tavern_points)
except ValueError:
    pass
else:
    raise AssertionError("reversed entrance depth was accepted")
print("PASS tavern: Y-up native GLB pivots and entrance-facing depth")

graybox = load_glb(HERE / "graybox" / "graybox_candidate.glb")
if len(graybox.get("skins", [])) != 1 or len(graybox.get("animations", [])) != 10:
    raise ValueError("graybox GLB skin or candidate animation count changed")
print("PASS graybox: glTF 2.0, one skin, ten animations, no required extensions")
