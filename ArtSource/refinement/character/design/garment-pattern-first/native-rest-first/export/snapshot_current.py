"""CPU snapshot of the live manifest-bound REST skin; never starts a producer."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT / "ArtSource/refinement/character/design/cuff-structure/motion-stage3"))
import audit_motion as gltf


def identity(path):
    path = Path(path)
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def rest_world(doc):
    parents = {c: i for i, n in enumerate(doc["nodes"]) for c in n.get("children", [])}
    world = np.empty((len(doc["nodes"]), 4, 4))
    seen = set()
    def visit(i):
        if i in seen:
            return
        local = gltf.local_matrix(doc["nodes"][i])
        if i in parents:
            visit(parents[i])
            world[i] = world[parents[i]] @ local
        else:
            world[i] = local
        seen.add(i)
    for i in range(len(world)):
        visit(i)
    return world


def main():
    manifest_path = ROOT / "ArtSource/tripo-warrior/motion_library.json"
    manifest = json.loads(manifest_path.read_text())
    entry = next(x for x in manifest["characters"] if x["id"] == "base")
    raw_path = (manifest_path.parent / entry["source"]).resolve()
    assert identity(raw_path)["sha256"] == entry["source_sha256"]
    library_path = manifest_path.parent / "library/characters.json"
    library = json.loads(library_path.read_text())
    base = next(x for x in library["characters"] if x["id"] == "base")
    outputs = {}
    for row in base["outputs"]:
        path = library_path.parent / row["file"]
        assert identity(path)["sha256"] == row["sha256"], row["file"]
        outputs[row["file"]] = identity(path)
    prepared_path = library_path.parent / "base_prepared_png.glb"
    published_path = ROOT / "app/src/main/assets/models/opponents/base.glb"
    if published_path.exists():
        assert identity(published_path)["sha256"] == outputs["base.glb"]["sha256"]
    raw, rb = gltf.load_glb(raw_path)
    prepared, pb = gltf.load_glb(prepared_path)
    assert len(raw["skins"]) == len(prepared["skins"]) == 1
    skin = raw["skins"][0]
    assert len(skin["joints"]) == 78
    assert raw["skins"] == prepared["skins"]
    names = [raw["nodes"][i]["name"] for i in skin["joints"]]
    assert len(set(names)) == 78
    rw, pw = rest_world(raw), rest_world(prepared)
    ibm = gltf.accessor(raw, rb, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    pibm = gltf.accessor(prepared, pb, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    assert np.array_equal(ibm, pibm)
    joint_ids = np.asarray(skin["joints"])
    for i in joint_ids:
        assert np.array_equal(gltf.local_matrix(raw["nodes"][int(i)]), gltf.local_matrix(prepared["nodes"][int(i)]))
    raw_skin_rest = rw[joint_ids] @ ibm
    prepared_skin_rest = pw[joint_ids] @ ibm
    guard_world = gltf.Sampler(prepared, pb, "idle").sample(0)
    arrays = {"bone_names": np.asarray(names), "joint_node_ids": joint_ids,
              "inverse_bind_matrices": ibm, "raw_joint_world_rest": rw[joint_ids],
              "prepared_joint_world_rest": pw[joint_ids], "raw_skin_rest_matrices": raw_skin_rest,
              "prepared_skin_rest_matrices": prepared_skin_rest,
              "prepared_guard_world": guard_world[joint_ids],
              "prepared_guard_skin_matrices": guard_world[joint_ids] @ ibm}
    palettes = []
    positive_counts = np.zeros(78, dtype=np.int64)
    for mi, mesh in enumerate(raw["meshes"]):
        for pi, prim in enumerate(mesh["primitives"]):
            attr = prim["attributes"]
            p = gltf.accessor(raw, rb, attr["POSITION"]).astype(float)
            j = gltf.accessor(raw, rb, attr["JOINTS_0"]).astype(np.int32)
            w = gltf.accessor(raw, rb, attr["WEIGHTS_0"]).astype(float)
            f = gltf.accessor(raw, rb, prim["indices"]).reshape(-1, 3).astype(np.int32)
            assert np.isfinite(p).all() and np.isfinite(w).all()
            assert np.max(abs(w.sum(axis=1) - 1)) < 2e-6
            referenced = np.unique(f)
            counts = np.bincount(j[referenced][w[referenced] > 0], minlength=78)
            positive_counts += counts
            palettes.append({"mesh": mi, "primitive": pi, "vertices": len(p), "referenced_vertices": len(referenced), "triangles": len(f),
                             "positive_bones": {names[i]: int(c) for i, c in enumerate(counts) if c}})
            key = f"raw_m{mi}_p{pi}"
            arrays.update({key+"_positions": p, key+"_joints": j, key+"_weights": w,
                           key+"_faces": f,
                           key+"_rest_world": gltf.lbs(p, j, w, prepared_skin_rest)})
            pp = prepared["meshes"][mi]["primitives"][pi]
            for semantic in ("POSITION", "JOINTS_0", "WEIGHTS_0"):
                assert np.array_equal(gltf.accessor(raw, rb, attr[semantic]),
                                      gltf.accessor(prepared, pb, pp["attributes"][semantic]))
    meshes = [i for i, n in enumerate(raw["nodes"]) if "mesh" in n]
    assert len(meshes) == 1
    mesh_id = meshes[0]
    arrays["raw_mesh_node_world_rest"] = rw[mesh_id]
    arrays["prepared_mesh_node_world_rest"] = pw[mesh_id]
    frame = pw[mesh_id] @ np.linalg.inv(rw[mesh_id])
    arrays["raw_world_to_prepared_world"] = frame
    assert np.allclose(pw[joint_ids], frame @ rw[joint_ids], atol=1e-12, rtol=0)
    snapshot = HERE / "current_rest_snapshot.npz"
    np.savez_compressed(snapshot, **arrays)
    report = {"status": "LIVE_MANIFEST_BOUND_REST_SNAPSHOT", "raw": identity(raw_path),
              "motion_library": identity(manifest_path), "library": identity(library_path),
              "outputs": outputs, "published": identity(published_path) if published_path.exists() else None,
              "snapshot": identity(snapshot), "frame": "prepared glTF world; metres, +Y up, +Z forward",
              "joint_count": 78, "joint_nodes_local_unchanged": True, "inverse_binds_byte_identical": True,
              "mesh_node_id": mesh_id, "raw_world_to_prepared_world": frame.tolist(),
              "attack_overhead": manifest["attack_source"]["clips"][0],
              "positive_weight_bones": {names[i]: int(c) for i, c in enumerate(positive_counts) if c},
              "unused_bones": [names[i] for i, c in enumerate(positive_counts) if not c],
              "primitive_palette": palettes,
              "raw_nodes": raw["nodes"], "raw_skins": raw["skins"], "raw_scenes": raw["scenes"],
              "prepared_normalization_nodes": prepared["nodes"][len(raw["nodes"]):],
              "limits": ["REST matrices are native node defaults, not idle@0.",
                         "Snapshot imports utility functions only; retired audit hard pins are never executed."]}
    (HERE / "current_rest_snapshot.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("raw", "outputs", "published", "snapshot", "joint_count", "unused_bones")}))


if __name__ == "__main__":
    main()
