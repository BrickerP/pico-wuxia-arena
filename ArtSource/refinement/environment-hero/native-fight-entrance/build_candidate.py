"""Replace the audited central entrance in frozen 64da; never run Blender.

Source BIN bytes are retained, including inactive old geometry. Budget numbers
describe active referenced geometry, not the size of that retained prefix.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
from verify_environment import read, rows, active_nodes, world_primitives
sys.path.insert(0, str(BASE / "single-window-integration-2026-11-12"))
from build_courtyard import Output, ModuleMerger
sys.path.insert(0, str(BASE / "facade-polish"))
from build_facade import budget
sys.path.insert(0, str(BASE / "stage2"))
from create_candidate import components, encode, tangents

SOURCE = BASE / "facade-polish/courtyard_facade_polish.glb"
MODULE = HERE / "entrance_module.glb"
SOURCE_SHA = "64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605"
EPS = 2e-6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds_for(center, size):
    center, size = np.array(center, float), np.array(size, float)
    return center - size / 2, center + size / 2


def matches(lo, hi, center, size, tolerance=2e-5):
    a, b = bounds_for(center, size)
    return np.allclose(lo, a, atol=tolerance, rtol=0) and np.allclose(hi, b, atol=tolerance, rtol=0)


def normalize_intersection(value):
    value = {k: v.copy() for k, v in value.items()}
    if "NORMAL" in value:
        normal = value["NORMAL"]
        normal /= max(np.linalg.norm(normal), 1e-20)
        if "TANGENT" in value:
            tangent = value["TANGENT"][:3]
            tangent -= normal * np.dot(normal, tangent)
            if np.linalg.norm(tangent) < 1e-10:
                tangent = np.eye(3)[int(np.argmin(np.abs(normal)))]
                tangent -= normal * np.dot(normal, tangent)
            value["TANGENT"][:3] = tangent / np.linalg.norm(tangent)
            value["TANGENT"][3] = 1 if value["TANGENT"][3] >= 0 else -1
    return value


def half(poly, axis, bound, sign=1, inside=True):
    """Inside owns the plane; outside excludes its tolerance band."""
    result = []
    if not poly:
        return result
    for a, b in zip(poly, poly[1:] + poly[:1]):
        da = (a["POSITION"][axis] - bound) * sign
        db = (b["POSITION"][axis] - bound) * sign
        ia = da >= -EPS if inside else da < -EPS
        ib = db >= -EPS if inside else db < -EPS
        if ia:
            result.append(a)
        if ia != ib:
            t = da / (da - db)
            result.append(normalize_intersection({k: a[k] + t * (b[k] - a[k]) for k in a}))
    return result


def outside_x(poly, low, high):
    left = half(poly, 0, low, 1, False)
    remaining = half(poly, 0, low, 1, True)
    right = half(remaining, 0, high, -1, False)
    return [left, right]


class Geometry:
    def __init__(self, attributes):
        self.values = {key: [] for key in attributes}
        self.indices = []
        self.discarded_degenerate = 0

    def emit(self, poly):
        for i in range(1, len(poly) - 1):
            tri = [poly[0], poly[i], poly[i + 1]]
            p = np.array([v["POSITION"] for v in tri], dtype=np.float32).astype(float)
            if np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) <= 1e-12:
                self.discarded_degenerate += 1
                continue
            start = len(self.values["POSITION"])
            self.indices.append([start, start + 1, start + 2])
            for v in tri:
                for key in self.values:
                    self.values[key].append(v[key])

    def write(self, out, target):
        if not self.indices:
            raise ValueError("A retained source primitive became empty")
        target["attributes"] = {
            key: out.accessor(values, "VEC" + str(len(values[0])))
            for key, values in self.values.items()
        }
        target["indices"] = out.accessor(np.asarray(self.indices).reshape(-1, 1), "SCALAR", True)


def component_records(doc, blob, mesh, primitive):
    p = doc["meshes"][mesh]["primitives"][primitive]
    pos = rows(doc, blob, p["attributes"]["POSITION"])
    ix = rows(doc, blob, p["indices"]).reshape(-1, 3)
    used = set(int(i) for i in ix.ravel())
    result = []
    for group in components(pos, ix):
        group = np.array([int(i) for i in group if int(i) in used], dtype=int)
        if len(group):
            result.append((group, pos[group].min(axis=0), pos[group].max(axis=0)))
    return p, pos, ix, result


def filtered_indices(out, mesh, primitive, ix, removed):
    keep = np.array([not any(int(i) in removed for i in tri) for tri in ix])
    out.doc["meshes"][mesh]["primitives"][primitive]["indices"] = out.accessor(ix[keep].reshape(-1, 1), "SCALAR", True)
    return int((~keep).sum())


def remove_doors(doc, blob, out):
    p, pos, ix, groups = component_records(doc, blob, 4, 3)
    handles = [g for g, lo, hi in groups if hi[1] < 1.2 and lo[1] > .9]
    if len(handles) != 2:
        raise ValueError("Expected exactly two central door handles")
    removed = set(np.concatenate(handles).tolist())
    count = filtered_indices(out, 4, 3, ix, removed)
    # Only the sign's gold strokes remain in this source mesh.
    retained = out.doc["meshes"][4]["primitives"][3]
    out.doc["meshes"][4]["primitives"] = [retained]
    if count != 216:
        raise ValueError("Unexpected handle triangle count")
    return {"removed_primitives": [0, 1, 2], "removed_handles": 2,
            "removed_triangles": sum(doc["accessors"][p["indices"]]["count"] // 3 for p in doc["meshes"][4]["primitives"][:3]) + count,
            "preserved": "12 gold sign strokes (528 triangles)"}


def trim_targets():
    targets = [((s * 1.29, 1.43, -5.17), (.055, 2.70, .085)) for s in (-1, 1)]
    targets.append(((0, 2.80, -5.17), (2.63, .085, .085)))
    for side in (-1, 1):
        for k in range(3):
            targets.append(((side * 1.4, 2.98 + k * .09, -4.855 + k * .15), (.30 + k * .04, .085, .022)))
        for dx in (-.09, .09):
            targets.append(((side * 1.4 + dx, 2.85, -5.085), (.022, .12, .028)))
    return targets


def remove_trim_caps_keys(doc, blob, out):
    reports = []
    targets = trim_targets()
    for pi in (0, 1):
        p, pos, ix, groups = component_records(doc, blob, 30, pi)
        removed = set()
        counts = [0] * len(targets)
        for g, lo, hi in groups:
            for j, (center, size) in enumerate(targets):
                a, b = bounds_for(center, size)
                # Octagonal face and bevel shells are disconnected in the old
                # producer. Select every indexed shell contained by each exact
                # logical box, including its separate endgrain front face.
                if np.all(lo >= a - 2e-5) and np.all(hi <= b + 2e-5):
                    removed.update(g.tolist())
                    counts[j] += 1
                    break
        if pi == 0 and any(c == 0 for c in counts):
            raise ValueError("A central trim/cap/key was not found: " + str(counts))
        reports.append({"primitive": pi, "logical_target_shell_counts": counts,
                        "removed_triangles": filtered_indices(out, 30, pi, ix, removed)})
    return reports


def edit_timber(doc, blob, out):
    reports = []
    for pi in (0, 1):
        p, pos, ix, groups = component_records(doc, blob, 22, pi)
        actions = {}
        counts = {"corbels": 0, "braces": 0, "pads": 0, "post_bases": 0, "low_beam": 0}
        for group, lo, hi in groups:
            action = None
            for side in (-1, 1):
                x = side * 1.4
                if pi == 0:
                    if matches(lo, hi, (x, 2.45, -5.24), (.23, 4.9, .29)):
                        action = "post_bases"
                    for k in range(3):
                        if matches(lo, hi, (x, 2.98 + k * .09, -5.10 + k * .10), (.32 + k * .04, .10, .48 + k * .10)):
                            action = "corbels"
                    if matches(lo, hi, (x, 2.69, -5.02), (.12, .4903448, .4744829)):
                        action = "braces"
                elif matches(lo, hi, (x, 2.94, -5.18), (.34, .16, .45)):
                    action = "pads"
            if pi == 0 and matches(lo, hi, (0, .43, -5.23), (11.7, .17, .25)):
                action = "low_beam"
            if action:
                counts[action] += 1
                for index in group:
                    actions[int(index)] = action
        expected = {"corbels": 6, "braces": 2, "pads": 0, "post_bases": 2, "low_beam": 1} if pi == 0 else {"corbels": 0, "braces": 0, "pads": 2, "post_bases": 0, "low_beam": 0}
        if counts != expected:
            raise ValueError("Timber component selection mismatch: " + str((pi, counts)))
        attrs = {k: rows(doc, blob, a) for k, a in p["attributes"].items()}
        geometry = Geometry(attrs)
        for tri in ix:
            poly = [{k: a[i].astype(float) for k, a in attrs.items()} for i in tri]
            action = actions.get(int(tri[0]))
            if action in ("corbels", "braces", "pads"):
                continue
            if action == "post_bases":
                geometry.emit(half(poly, 1, .285))
            elif action == "low_beam":
                for part in outside_x(poly, -1.285, 1.285):
                    geometry.emit(part)
            else:
                geometry.emit(poly)
        geometry.write(out, out.doc["meshes"][22]["primitives"][pi])
        reports.append({"primitive": pi, "selected_components": counts,
                        "output_triangles": len(geometry.indices), "cut_surfaces": "post Y=.285 and beam X=+/-1.285; covered by the new entrance construction"})
    return reports


def edit_stone(doc, blob, out):
    p, pos, ix, groups = component_records(doc, blob, 23, 1)
    actions = {}
    counts = {"bases": 0, "steps": 0, "terrace": 0}
    for group, lo, hi in groups:
        action = None
        if any(matches(lo, hi, (s * 1.4, .16, -5.22), (.40, .32, .43)) for s in (-1, 1)):
            action = "bases"
        if matches(lo, hi, (0, .035, -4.94), (2.78, .07, .32)) or matches(lo, hi, (0, .07, -5.20), (2.78, .14, .32)):
            action = "steps"
        if matches(lo, hi, (0, .06, -5.12), (11.8, .12, .88)):
            action = "terrace"
        if action:
            counts[action] += 1
            for index in group:
                actions[int(index)] = action
    if counts != {"bases": 2, "steps": 2, "terrace": 1}:
        raise ValueError("Stone component selection mismatch: " + str(counts))
    attrs = {k: rows(doc, blob, a) for k, a in p["attributes"].items()}
    geometry = Geometry(attrs)
    for tri in ix:
        poly = [{k: a[i].astype(float) for k, a in attrs.items()} for i in tri]
        action = actions.get(int(tri[0]))
        if action in ("bases", "steps"):
            continue
        if action == "terrace":
            for part in outside_x(poly, -1.62, 1.62):
                geometry.emit(part)
        else:
            geometry.emit(poly)
    # The terrace's new ends face the doorway and are visible. Close the
    # actual 4mm-bevel octagonal section instead of leaving hollow shells.
    section=[(0,-5.556),(0,-4.684),(.004,-4.68),(.116,-4.68),
             (.12,-4.684),(.12,-5.556),(.116,-5.56),(.004,-5.56)]
    for x,nx in [(-1.62,1),(1.62,-1)]:
        cap=[]
        for y,z in section:
            q={"POSITION":np.array([x,y,z]),"NORMAL":np.array([nx,0.,0.]),
               "TEXCOORD_0":np.array([z/.65,y/.65])}
            if "TANGENT" in attrs:q["TANGENT"]=np.array([0.,0.,1.,-nx])
            if set(q)!=set(attrs):raise ValueError("Unsupported terrace cap attribute layout")
            cap.append(q)
        geometry.emit(list(reversed(cap)) if nx>0 else cap)
    geometry.write(out, out.doc["meshes"][23]["primitives"][1])
    return {"selected_components": counts, "terrace_cut_x": [-1.62, 1.62],
            "closed_terrace_cut_faces":2,"added_cap_triangles":12,
            "output_triangles": len(geometry.indices)}


def prepare_module(doc, blob):
    out = Output(copy.deepcopy(doc), blob)
    reports = []
    used_meshes = {doc["nodes"][i]["mesh"] for i in active_nodes(doc) if "mesh" in doc["nodes"][i]}
    if doc.get("skins") or doc.get("animations"):
        raise ValueError("Entrance module must be static")
    for mi in used_meshes:
        for pi, p in enumerate(out.doc["meshes"][mi]["primitives"]):
            if p.get("mode", 4) != 4:
                raise ValueError("Entrance requires triangle primitives")
            attrs = p["attributes"]
            pos = rows(out.doc, out.blob, attrs["POSITION"]).astype(np.float32)
            ix = rows(out.doc, out.blob, p["indices"]).reshape(-1, 3)
            t = pos[ix].astype(float)
            keep = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) > 1e-12
            if not keep.any():
                raise ValueError("Entrance module contains an empty primitive")
            removed = int((~keep).sum())
            ix = ix[keep]
            if removed:
                p["indices"] = out.accessor(ix.reshape(-1, 1), "SCALAR", True)
            if not all(np.isfinite(rows(out.doc, out.blob, a)).all() for a in attrs.values()):
                raise ValueError("Entrance module contains non-finite attributes")
            added = False
            if "normalTexture" in out.doc["materials"][p["material"]] and "TANGENT" not in attrs:
                if "NORMAL" not in attrs or "TEXCOORD_0" not in attrs:
                    raise ValueError("Normal-mapped entrance primitive lacks N/UV")
                n = rows(out.doc, out.blob, attrs["NORMAL"])
                uv = rows(out.doc, out.blob, attrs["TEXCOORD_0"])
                fallback = np.tile([1., 0., 0., 1.], (len(pos), 1))
                fallback[np.abs(n[:, 0]) > .95, :3] = [0, 0, 1]
                ts = tangents(pos, n, uv, ix, fallback)
                if not np.isfinite(ts).all() or np.max(np.abs(np.sum(ts[:, :3] * n, axis=1))) > 1e-4:
                    raise ValueError("Entrance tangent basis is invalid")
                attrs["TANGENT"] = out.accessor(ts, "VEC4")
                added = True
            reports.append({"mesh": mi, "primitive": pi, "removed_f32_degenerate": removed, "added_tangent": added})
    return out.doc, out.blob, reports


def self_test():
    def vertex(x, y):
        return {"POSITION": np.array([x, y, 0.]), "NORMAL": np.array([0., 0., 1.]), "TEXCOORD_0": np.array([x, y])}
    poly = [vertex(-2, 0), vertex(2, 0), vertex(0, 2)]
    result = half(poly, 0, 0)
    assert len(result) >= 3 and all(p["POSITION"][0] >= -EPS for p in result)
    g = Geometry(poly[0])
    for part in outside_x(poly, -3, 3):
        g.emit(part)
    assert not g.indices
    assert matches(np.array([-1., -1., -1.]), np.array([1., 1., 1.]), (0, 0, 0), (2, 2, 2))
    assert not matches(np.zeros(3), np.ones(3), (0, 0, 0), (2, 2, 2))
    print("SELF_TEST_PASS: clipping, fully removed slab, strict component bounds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError("Frozen source64da SHA mismatch")
    module_sha = sha(MODULE)  # Current authored module; intentionally not pinned to an earlier iteration.
    doc, blob = read(SOURCE)
    for name in ("EH_EntryDoorsWindows", "EH_TavernTimber", "EH_TavernWalls", "EH_S2_TimberJointFaces"):
        ni = next(i for i, n in enumerate(doc["nodes"]) if n.get("name") == name)
        np.testing.assert_allclose(active_nodes(doc)[ni], np.eye(4), atol=1e-8)
    out = Output(copy.deepcopy(doc), blob)
    report = {"door": remove_doors(doc, blob, out), "trim_caps_keys": remove_trim_caps_keys(doc, blob, out),
              "timber": edit_timber(doc, blob, out), "stone": edit_stone(doc, blob, out)}
    md, mb = read(MODULE)
    md, mb, module_report = prepare_module(md, mb)
    merger = ModuleMerger(out, md, mb)
    children = [merger.node(i) for i in md["scenes"][md.get("scene", 0)]["nodes"]]
    root = out.doc["scenes"][out.doc.get("scene", 0)]["nodes"][0]
    out.doc["nodes"].append({"name": "NativeFightEntrance_Root", "children": children})
    out.doc["nodes"][root].setdefault("children", []).append(len(out.doc["nodes"]) - 1)
    if len(out.doc["materials"]) != 32 or len(out.doc["images"]) != 50:
        raise ValueError("Module must reuse source materials/images exactly: " + str((len(out.doc["materials"]), len(out.doc["images"]))))
    result_budget = budget(out.doc, out.blob)
    if result_budget["node_expanded_triangles"] > 250000:
        raise ValueError("Candidate exceeds 250k active expanded triangles")
    output = HERE / "courtyard_native_entrance.glb"
    data = encode(out.doc, out.blob)
    # Do not publish a candidate assembled from an input being regenerated.
    if sha(SOURCE) != SOURCE_SHA or sha(MODULE) != module_sha:
        raise ValueError("An input changed during assembly; retry after its author finishes")
    output.write_bytes(data)
    audit = {"status": "built_for_root_verification", "candidate": output.name, "sha256": sha(output),
             "source_sha256": SOURCE_SHA, "module_sha256": module_sha, "producer_sha256": sha(Path(__file__)),
             "placement_stage_m": [0, 0, 0], "rotation": "identity", "scale": [1, 1, 1],
             "source_budget": budget(doc, blob), "candidate_budget": result_budget, "source_bytes": SOURCE.stat().st_size,
             "candidate_bytes": len(data), "source_binary_prefix_retained": True,
             "resource_policy": "source BIN including inactive bytes retained; no global repack or batching",
             "selection": report, "module_cleanup": module_report, "module_resource_maps": merger.maps,
             "unchanged": ["nine window instances", "ground receivers and Y=0", "all original nodes/transforms/anchors", "NPC placement is a separate Root-owned resource"],
             "native_validation": "pending Root; script does not build or operate a device"}
    text = json.dumps(audit, indent=2) + "\n"
    if len(text.encode()) > 250000:
        raise ValueError("Audit unexpectedly exceeds 250kB")
    (HERE / "audit.json").write_text(text)
    print(json.dumps({"candidate": str(output), "sha256": audit["sha256"], "budget": result_budget}, indent=2))


if __name__ == "__main__":
    main()
