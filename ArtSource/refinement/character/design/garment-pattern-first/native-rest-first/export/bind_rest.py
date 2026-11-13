"""Bind a complete constructed REST garment to the live 78-joint native skin.

All writes are private export artifacts. The standalone deliverable keeps native
raw mesh coordinates plus the current canonical normalization parent. It has no
animation or body/context geometry. The separate review copy adds actual idle
samplers without changing its defaults.
"""
from pathlib import Path
import argparse
import copy
import json
import struct
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
sys.path.insert(0, str(HERE))
from snapshot_current import identity, rest_world, gltf


def write_glb(path, doc, binary):
    doc["buffers"] = [{"byteLength": len(binary)}]
    encoded = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    data = struct.pack("<III", 0x46546C67, 2, 28 + len(encoded) + len(binary))
    data += struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
    data += struct.pack("<II", len(binary), 0x004E4942) + binary
    path.write_bytes(data)


def append_array(doc, binary, values, kind, component=5126, target=None):
    values = np.asarray(values, dtype={5126: "<f4", 5123: "<u2", 5125: "<u4"}[component])
    binary.extend(b"\0" * (-len(binary) % 4))
    view = {"buffer": 0, "byteOffset": len(binary), "byteLength": values.nbytes}
    if target:
        view["target"] = target
    binary.extend(values.tobytes())
    vi = len(doc.setdefault("bufferViews", []))
    doc["bufferViews"].append(view)
    count = len(values)
    a = {"bufferView": vi, "componentType": component, "count": count, "type": kind}
    if kind == "VEC3" and target == 34962:
        a.update(min=values.min(axis=0).tolist(), max=values.max(axis=0).tolist())
    ai = len(doc.setdefault("accessors", []))
    doc["accessors"].append(a)
    return ai


def normals(points, faces):
    tri = points[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    assert np.linalg.norm(n, axis=1).min() > 1e-12
    out = np.zeros_like(points)
    for i in range(3):
        np.add.at(out, faces[:, i], n)
    length = np.linalg.norm(out, axis=1)
    assert length.min() > 1e-12
    return out / length[:, None]


def transfer_weights(points, snapshot, remove):
    """Transfer only actual upper-body influences from verified old cloth.

    Four nearest referenced source vertices give a continuous starting field.
    Unique joint contributions are summed before retaining the four largest.
    Unused helpers and all finger/hand/head/leg influences are excluded.
    """
    names = snapshot["bone_names"].tolist()
    allowed_names = ["Pelvis", "Waist", "Spine01", "Spine02", "L_Clavicle", "L_Upperarm", "L_Forearm",
                     "R_Clavicle", "R_Upperarm", "R_Forearm"]
    allowed = np.array([names.index(n) for n in allowed_names])
    p = snapshot["raw_m0_p0_rest_world"]
    j = snapshot["raw_m0_p0_joints"]
    w = snapshot["raw_m0_p0_weights"]
    source_ids = np.unique(snapshot["raw_m0_p0_faces"][remove])
    allowed_w = w * np.isin(j, allowed)
    mass = allowed_w.sum(axis=1)
    source_ids = source_ids[mass[source_ids] > .95]
    source_points = p[source_ids]
    dense = np.zeros((len(source_ids), 78))
    for slot in range(4):
        dense[np.arange(len(source_ids)), j[source_ids, slot]] += allowed_w[source_ids, slot]
    dense /= dense.sum(axis=1)[:, None]
    nearest_ids, nearest_d = [], []
    joint_rows, weight_rows = [], []
    for start in range(0, len(points), 128):
        block = points[start:start+128]
        d2 = np.sum((block[:, None, :] - source_points[None, :, :]) ** 2, axis=2)
        near = np.argpartition(d2, 3, axis=1)[:, :4]
        dist = np.take_along_axis(d2, near, axis=1)
        order = np.argsort(dist, axis=1)
        near = np.take_along_axis(near, order, axis=1)
        dist = np.take_along_axis(dist, order, axis=1)
        blend = 1 / np.maximum(dist, 1e-10)
        blend /= blend.sum(axis=1)[:, None]
        weights = np.einsum("vk,vkj->vj", blend, dense[near])
        top = np.argsort(-weights, axis=1, kind="stable")[:, :4]
        topw = np.take_along_axis(weights, top, axis=1)
        topw /= topw.sum(axis=1)[:, None]
        top[topw < 1e-8] = 0
        topw[topw < 1e-8] = 0
        topw /= topw.sum(axis=1)[:, None]
        joint_rows.append(top)
        weight_rows.append(topw)
        nearest_ids.append(source_ids[near])
        nearest_d.append(np.sqrt(dist))
    return (np.concatenate(joint_rows).astype(np.uint16), np.concatenate(weight_rows).astype(np.float32),
            np.concatenate(nearest_ids), np.concatenate(nearest_d), allowed_names)


def canonical_wrappers(doc, prepared):
    roots = doc["scenes"][doc.get("scene", 0)]["nodes"]
    frame = copy.deepcopy(next(n for n in prepared["nodes"] if n.get("name") == "TripoBody_Root"))
    frame["children"] = roots
    i = len(doc["nodes"])
    doc["nodes"].append(frame)
    doc["nodes"].append({"name": "TripoWarrior_Root", "children": [i]})
    doc["scenes"] = [{"name": "Native REST garment", "nodes": [i + 1]}]
    doc["scene"] = 0


def copy_idle(doc, binary, prepared, pb):
    clip = copy.deepcopy(next(x for x in prepared["animations"] if x["name"] == "idle"))
    copied = {}
    for sampler in clip["samplers"]:
        for field in ("input", "output"):
            index = sampler[field]
            if index not in copied:
                accessor = copy.deepcopy(prepared["accessors"][index])
                view = prepared["bufferViews"][accessor["bufferView"]]
                assert not view.get("byteStride") and not accessor.get("byteOffset", 0)
                begin = view.get("byteOffset", 0)
                binary.extend(b"\0" * (-len(binary) % 4))
                vi = len(doc["bufferViews"])
                doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": view["byteLength"]})
                binary.extend(pb[begin:begin + view["byteLength"]])
                accessor["bufferView"] = vi
                copied[index] = len(doc["accessors"])
                doc["accessors"].append(accessor)
            sampler[field] = copied[index]
    doc["animations"] = [clip]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", type=Path, required=True)
    args = ap.parse_args()
    handoff_path = args.structure.parent / "structure_handoff.json"
    handoff = json.loads(handoff_path.read_text())
    if handoff["status"] != "REST_STRUCTURE_READY_FOR_BINDING":
        raise SystemExit("STOP: upstream REST structure failed. No binding, GLB or render is authorized.")
    assert handoff["proper_crossing_count"] == 0
    assert handoff["nonmanifold_edges"] == handoff["bad_vertex_links"] == handoff["degenerate_faces"] == 0
    assert identity(args.structure)["sha256"] == handoff["output"]["sha256"]
    report = json.loads((HERE / "current_rest_snapshot.json").read_text())
    for entry in [report["raw"], report["motion_library"], report["library"], report["published"], *report["outputs"].values(), report["snapshot"]]:
        assert identity(ROOT / entry["path"])["sha256"] == entry["sha256"], entry["path"]
    s = np.load(ROOT / report["snapshot"]["path"])
    structure = np.load(args.structure)
    target = structure["positions_rest"].astype(float)
    faces = structure["triangles"].astype(np.int32)
    assert np.isfinite(target).all() and len(target) > 6000
    assert np.array_equal(structure["bone_names"], s["bone_names"])
    assert np.allclose(structure["current_rest_bone_world"], s["prepared_joint_world_rest"], atol=1e-10, rtol=0)
    raw, rb = gltf.load_glb(ROOT / report["raw"]["path"])
    prepared, pb = gltf.load_glb(ROOT / report["outputs"]["base_prepared_png.glb"]["path"])
    remove_path = ROOT / "ArtSource/refinement/character/design/upperbody-2026-11-12/shape-r2/current_remove.npz"
    removal = np.load(remove_path)
    remove_key = next(k for k in removal.files if "row" in k)
    remove = removal[remove_key].astype(int)
    assert len(remove) == len(np.unique(remove)) == 17157
    assert np.array_equal(s["raw_m0_p0_faces"][remove], removal["current_primitive_0_vertex_triplets"])
    joints, weights, source_ids, source_distance, allowed = transfer_weights(target, s, remove)
    # Solve the actual weighted REST skin matrix per point. No guard is inverted.
    matrices = np.sum(s["prepared_skin_rest_matrices"][joints] * weights[:, :, None, None], axis=1)
    local4 = np.linalg.solve(matrices, np.column_stack((target, np.ones(len(target))))[:, :, None])[:, :, 0]
    local = (local4[:, :3] / local4[:, 3, None]).astype(np.float32)
    local_normals = normals(local.astype(float), faces).astype(np.float32)
    restored = gltf.lbs(local, joints, weights, s["prepared_skin_rest_matrices"])
    rest_error = np.linalg.norm(restored - target, axis=1)
    assert rest_error.max() < 2e-7
    assert np.max(abs(weights.sum(axis=1) - 1)) < 2e-7
    for j, w in zip(joints, weights):
        assert len(set(j[w > 0].tolist())) == (w > 0).sum()
    used = set(joints[weights > 0].tolist())
    assert all(s["bone_names"][i] in report["positive_weight_bones"] for i in used)
    # Native standalone: current original hierarchy and IBM, only one new mesh.
    doc = {"asset": {"version": "2.0", "generator": "Native REST garment private candidate"},
           "nodes": copy.deepcopy(raw["nodes"]), "scenes": copy.deepcopy(raw["scenes"]),
           "scene": raw.get("scene", 0), "skins": copy.deepcopy(raw["skins"]), "accessors": [], "bufferViews": [],
           "materials": [{"name": "Untextured REST garment", "doubleSided": True,
                          "pbrMetallicRoughness": {"baseColorFactor": [.34, .36, .38, 1], "metallicFactor": 0, "roughnessFactor": .8}}]}
    binary = bytearray()
    ibm_values = s["inverse_bind_matrices"].transpose(0, 2, 1).reshape(-1, 16)
    doc["skins"][0]["inverseBindMatrices"] = append_array(doc, binary, ibm_values, "MAT4")
    attrs = {"POSITION": append_array(doc, binary, local, "VEC3", target=34962),
             "NORMAL": append_array(doc, binary, local_normals, "VEC3", target=34962),
             "JOINTS_0": append_array(doc, binary, joints, "VEC4", 5123, 34962),
             "WEIGHTS_0": append_array(doc, binary, weights, "VEC4", target=34962)}
    prim = {"attributes": attrs, "indices": append_array(doc, binary, faces.ravel(), "SCALAR", 5125, 34963), "material": 0}
    doc["meshes"] = [{"name": "Complete native REST garment", "primitives": [prim]}]
    mesh_id = report["mesh_node_id"]
    doc["nodes"][mesh_id]["name"] = "Native_REST_Garment_Mesh"
    assert doc["nodes"][mesh_id]["mesh"] == 0
    canonical_wrappers(doc, prepared)
    standalone = HERE / "garment_native_rest.glb"
    write_glb(standalone, doc, binary)
    output_doc, output_bin = gltf.load_glb(standalone)
    output_world = rest_world(output_doc)
    output_ibm = gltf.accessor(output_doc, output_bin, 0).reshape(-1, 4, 4).transpose(0, 2, 1)
    assert np.array_equal(output_ibm, s["inverse_bind_matrices"])
    assert np.allclose(output_world[s["joint_node_ids"]], s["prepared_joint_world_rest"], atol=1e-12, rtol=0)
    assert "animations" not in output_doc and len(output_doc["meshes"]) == 1
    # Separate preview supplies genuine current idle curves, never baked points.
    preview_doc, preview_bin = copy.deepcopy(doc), bytearray(binary)
    copy_idle(preview_doc, preview_bin, prepared, pb)
    preview = HERE / "garment_guard_review.glb"
    write_glb(preview, preview_doc, preview_bin)
    guard = gltf.lbs(local, joints, weights, s["prepared_guard_skin_matrices"])
    np.savez_compressed(HERE / "binding_arrays.npz", positions_raw_local=local, positions_rest=target,
                        normals_raw_local=local_normals, triangles=faces, joints=joints, weights=weights,
                        source_vertex_ids=source_ids, source_distance_m=source_distance, positions_guard=guard)
    result = {"status": "NATIVE_REST_SKIN_BOUND_PENDING_GUARD_REVIEW", "structure": identity(args.structure),
              "current_snapshot": identity(HERE / "current_rest_snapshot.json"), "raw": report["raw"],
              "prepared": report["outputs"]["base_prepared_png.glb"], "published": report["published"],
              "garment": identity(standalone), "guard_review_only": identity(preview),
              "arrays": identity(HERE / "binding_arrays.npz"), "vertices": len(target), "triangles": len(faces),
              "rest_reconstruction_max_m": float(rest_error.max()), "native_78_rest_and_ibm_preserved": True,
              "positive_joint_names": [s["bone_names"][i] for i in sorted(used)],
                    "weight_source": "Four nearest current raw referenced work-cloth selection vertices in canonical REST, merged unique influences and top4",
              "source_filter_allowed_bones": allowed, "max_unique_positive_weights": int((weights > 0).sum(axis=1).max()),
              "source_nearest_distance_m": {"max": float(source_distance[:, 0].max()), "p95": float(np.quantile(source_distance[:, 0], .95))},
              "mesh_geometry_scope": "garment only; no head, hands, body, pants, context or DAO geometry",
              "integration_contract": {"owner": "Root", "raw_source": report["raw"], "skin": 0,
                    "joint_order": s["bone_names"].tolist(), "coordinate_space": "Original raw mesh-local bind coordinates",
                    "action": "Append garment primitive attributes/indices to the current raw mesh; preserve native raw nodes and IBM. Do not copy canonical wrapper into raw.",
                    "normalization": "Root producer computes canonical normalization from combined raw. Preserve original body geometry to retain bounds.",
                    "old_cloth_removal": {"source": identity(remove_path), "p0_face_rows": len(remove),
                         "authority": "Current ordered triplets revalidated independently; no old SHA assumption",
                         "full_removal_certified": False, "remaining_unconfirmed_group0_faces": 1009},
                    "preserve": "All original raw attributes byte-identical; p1..8 all faces, protected p0 all incident faces; original face/hands/waist/pants"},
              "limits": ["Actual guard import/78-bone and surface validation pending.", "No dynamic pass, UV, bake, material or art approval.",
                         "Conservative old-cloth removal does not prove all old right wrist rings removed."]}
    (HERE / "binding_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "garment", "vertices", "triangles", "rest_reconstruction_max_m", "positive_joint_names")}))


if __name__ == "__main__":
    main()
