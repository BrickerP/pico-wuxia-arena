"""Independent hero grip preservation, real skin contact and blade-path audit.

Run inside Blender. Only audit.json in this directory is written.
"""

import copy
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
REPO = GRIP.parents[2]
sys.path.insert(0, str(GRIP))
sys.path.insert(0, str(REPO / "ArtSource/tripo-warrior"))

import numpy as np
from measure_weapon_surface import measure_left_weapon
from prepare_character_library import decode_animation, node_order, sampled_local
from prepare_rigged_warrior import local_matrix, read_glb
from refine_character_grips import accessor, pose_clouds, summarize

SOURCE_HASH = "5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f"
SOURCE = REPO / "ArtSource/tripo-warrior/library/base.glb"
CANDIDATE = HERE / "candidates/base.glb"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix(node):
    return np.array(list(local_matrix(node)), dtype=float)


def quaternion_angle(a, b):
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    a /= np.linalg.norm(a)
    b /= np.linalg.norm(b)
    return math.degrees(2 * math.acos(min(1.0, float(abs(a @ b)))))


def verify_preservation(source, original, candidate, binary, alignment):
    require(len(source["skins"][0]["joints"]) == len(candidate["skins"][0]["joints"]) == 78, "joint count changed")
    grip = next(index for index, node in enumerate(source["nodes"]) if node.get("name") == "HandGrip_R")
    require(len(source["nodes"]) == len(candidate["nodes"]), "node count changed")
    for index, (old, new) in enumerate(zip(source["nodes"], candidate["nodes"])):
        if index != grip:
            require(old == new, "body/rest/anchor node changed: " + old.get("name", str(index)))
    old_mount, new_mount = matrix(source["nodes"][grip]), matrix(candidate["nodes"][grip])
    require(np.max(abs(old_mount[:3, :3] - new_mount[:3, :3])) < 1e-7, "grip orientation or scale changed")
    require(np.max(abs(old_mount[3] - new_mount[3])) < 1e-7, "grip homogeneous row changed")
    old_marker, new_marker = copy.deepcopy(source["nodes"][grip]), copy.deepcopy(candidate["nodes"][grip])
    for row in (old_marker, new_marker):
        row.pop("matrix", None)
        row.pop("translation", None)
    require(old_marker == new_marker, "grip marker hierarchy or other fields changed")
    for field in ("skins", "materials", "textures", "images", "scenes", "scene"):
        require(source.get(field) == candidate.get(field), "preserved field changed: " + field)
    require(binary[:len(original)] == original, "original body/skin/weight/time binary changed")
    require(candidate["accessors"][:len(source["accessors"])] == source["accessors"], "old accessor metadata changed")
    require(candidate["bufferViews"][:len(source["bufferViews"])] == source["bufferViews"], "old buffer views changed")
    require(len(source["meshes"]) == len(candidate["meshes"]), "mesh count changed")
    body_mesh = next(node["mesh"] for node in source["nodes"] if node.get("name") == "TripoBody_Mesh")
    weapon_indices = alignment["weapon_binding"]["weapon_primitive_indices"]
    adjusted_meshes = copy.deepcopy(candidate["meshes"])
    translations = []
    for index in weapon_indices:
        old = source["meshes"][body_mesh]["primitives"][index]
        new = candidate["meshes"][body_mesh]["primitives"][index]
        old_positions = accessor(source, original, old["attributes"]["POSITION"])
        new_positions = accessor(candidate, binary, new["attributes"]["POSITION"])
        require(old_positions.shape == new_positions.shape, "weapon geometry count changed")
        difference = new_positions.astype(float) - old_positions.astype(float)
        translations.append(difference)
        adjusted_meshes[body_mesh]["primitives"][index]["attributes"]["POSITION"] = old["attributes"]["POSITION"]
    require(source["meshes"] == adjusted_meshes, "body/topology/weights/normals/materials changed")
    shifts = np.concatenate(translations)
    actual_shift = np.mean(shifts, axis=0)
    require(np.max(np.linalg.norm(shifts - actual_shift, axis=1)) < 2e-6, "weapon is deformed rather than translated")
    joints = source["skins"][0]["joints"]
    hand = next(i for i, node in enumerate(source["nodes"]) if node.get("name") == "R_Hand")
    hand_palette = joints.index(hand)
    binds = accessor(source, original, source["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    delta_hand = new_mount[:3, 3] - old_mount[:3, 3]
    expected_shift = np.linalg.inv(binds[hand_palette])[:3, :3] @ delta_hand
    require(np.linalg.norm(actual_shift - expected_shift) < 2e-6, "skin translation and grip marker disagree")
    require(len(source["animations"]) == len(candidate["animations"]) == 8, "clip count changed")
    prefixes = tuple(side + finger for side in ("R_", "L_") for finger in ("Thumb", "Index", "Mid", "Ring", "Pinky"))
    changes = []
    for old, new in zip(source["animations"], candidate["animations"]):
        require(old["name"] == new["name"] and old["channels"] == new["channels"], "clip identity/targets changed")
        require(len(old["samplers"]) == len(new["samplers"]), "sampler count changed")
        for channel in old["channels"]:
            before, after = old["samplers"][channel["sampler"]], new["samplers"][channel["sampler"]]
            name = source["nodes"][channel["target"]["node"]].get("name", "")
            require(before["input"] == after["input"] and before.get("interpolation") == after.get("interpolation"), "action time/interpolation changed")
            if before == after:
                continue
            require(channel["target"]["path"] == "rotation" and name.startswith(prefixes), "nonfinger animation changed: " + name)
            a = accessor(source, original, before["output"])
            b = accessor(candidate, binary, after["output"])
            require(a.shape == b.shape and np.isfinite(b).all(), "finger sample shape/finite check failed")
            require(np.max(abs(np.linalg.norm(b, axis=1) - 1)) < 1e-5, "finger quaternion is not unit")
            maximum = max(quaternion_angle(x, y) for x, y in zip(a, b))
            require(maximum <= 18.001, "finger rotation exceeds reviewed bound")
            changes.append({"clip": old["name"], "bone": name, "maximum_local_rotation_delta_degrees": maximum})
    return {"rest_body_skin_weights_inverse_binds_exact": True,
        "action_time_inputs_and_nonfinger_animation_exact": True,
        "grip_and_blade_orientation_preserved": True,
        "weapon_bind_space_translation": actual_shift.tolist(),
        "grip_local_translation_metres": np.linalg.solve(old_mount[:3, :3], delta_hand).tolist(),
        "maximum_weapon_translation_nonuniformity_metres": float(np.max(np.linalg.norm(shifts - actual_shift, axis=1))),
        "changed_finger_rotation_tracks": changes}


def right_metrics(document, binary, alignment):
    clouds, masks, count = pose_clouds(document, binary, alignment, local_matrix({"matrix": alignment["grip_local_matrix_gltf"]}))
    result = summarize(clouds, masks, np.zeros(3))
    return {"metric": "authored elliptical handle radial sample proxy, not penetration depth",
            "hand_samples": count, "sampled_pose_count": len(clouds),
            **{key: value for key, value in result.items() if key != "poses"},
            "native_contact_2_117": next(cloud["published"] for cloud in clouds if cloud["clip"] == "slash" and cloud["time_seconds"] == 2.117),
            "pose_measurements": [{"clip": cloud["clip"], "time_seconds": cloud["time_seconds"], "metrics": result["poses"][i]}
                                  for i, cloud in enumerate(clouds)]}


def blade_translation(source, old_binary, candidate, binary):
    decoded = []
    for document, packed in ((source, old_binary), (candidate, binary)):
        clip = next(clip for clip in document["animations"] if clip["name"] == "slash")
        tracks, _ = decode_animation({**document, "animations": [clip]}, packed)
        parents, order = node_order(document)
        tip = next(i for i, node in enumerate(document["nodes"]) if node.get("name") == "Blade_Tip")
        decoded.append((tracks, parents, order, tip))
    rows = []
    for time in sorted({1.55, 2.117, 3.4, *[frame / 60 for frame in range(93, 205)]}):
        endpoints = []
        for document, (tracks, parents, order, tip) in zip((source, candidate), decoded):
            world = {}
            for index in order:
                local = sampled_local(document["nodes"][index], index, tracks, time)
                world[index] = world[parents[index]] @ local if index in parents else local
            endpoints.append(np.array(world[tip].translation))
        shift = endpoints[1] - endpoints[0]
        rows.append({"time_seconds": time, "before_tip_metres": endpoints[0].tolist(),
                     "after_tip_metres": endpoints[1].tolist(), "translation_mm": float(np.linalg.norm(shift) * 1000)})
    return {"source_contact_time_seconds": 2.117, "contact_time_preserved": True,
            "physical_contact_position_requires_main_reassessment": True,
            "maximum_blade_tip_translation_mm": max(row["translation_mm"] for row in rows), "samples": rows}


def main():
    source_hash, candidate_hash = sha(SOURCE), sha(CANDIDATE)
    require(source_hash == SOURCE_HASH, "hero source identity changed")
    source, old_binary = read_glb(SOURCE)
    candidate, binary = read_glb(CANDIDATE)
    alignment = json.loads((REPO / "ArtSource/tripo-warrior/library/base_alignment.json").read_text())
    candidate_alignment = json.loads((HERE / "alignment.json").read_text())
    marker = next(node for node in candidate["nodes"] if node.get("name") == "HandGrip_R")
    require(np.max(abs(np.array(candidate_alignment["grip_local_matrix_gltf"]) - np.array(marker["matrix"]))) < 1e-7,
            "candidate alignment differs from actual grip marker")
    result = {"scope": "hero60k fixed source, finger rotation and translated rigid grip only; offline discrete evidence",
        "source_sha256": source_hash, "candidate_sha256": candidate_hash,
        "invariants": verify_preservation(source, old_binary, candidate, binary, alignment)}
    result["right_before"] = right_metrics(source, old_binary, alignment)
    result["right_after"] = right_metrics(candidate, binary, candidate_alignment)
    times = sorted({1 + frame / 120 for frame in range(361)} | {1.55, 2.117, 3.4})
    poses = [("slash", time) for time in times]
    result["left_before"] = measure_left_weapon(source, old_binary, alignment, poses)
    result["left_after"] = measure_left_weapon(candidate, binary, candidate_alignment, poses)
    result["left_crossing_regressions"] = [
        {"time_seconds": new["time_seconds"], "before": old["groups"]["whole_dao"], "after": new["groups"]["whole_dao"]}
        for old, new in zip(result["left_before"]["pose_measurements"], result["left_after"]["pose_measurements"])
        if new["groups"]["whole_dao"]["confirmed_noncoplanar_triangle_crossing_pairs"] >
        old["groups"]["whole_dao"]["confirmed_noncoplanar_triangle_crossing_pairs"]]
    result["blade_translation"] = blade_translation(source, old_binary, candidate, binary)
    require(source_hash == sha(SOURCE) and candidate_hash == sha(CANDIDATE), "files changed during independent audit")
    result["files_stable_during_audit"] = True
    result["continuous_clearance_proven"] = False
    (HERE / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("HERO_AUDIT", json.dumps({
        "source_sha256": source_hash, "candidate_sha256": candidate_hash,
        "right_before": {k: v for k, v in result["right_before"].items() if k not in ("pose_measurements", "native_contact_2_117")},
        "right_after": {k: v for k, v in result["right_after"].items() if k not in ("pose_measurements", "native_contact_2_117")},
        "left_before_max_crossings": result["left_before"]["maximum_confirmed_triangle_crossing_pairs"],
        "left_after_max_crossings": result["left_after"]["maximum_confirmed_triangle_crossing_pairs"],
        "left_regression_poses": len(result["left_crossing_regressions"]),
        "maximum_blade_tip_translation_mm": result["blade_translation"]["maximum_blade_tip_translation_mm"],
    }), flush=True)


if __name__ == "__main__":
    main()
