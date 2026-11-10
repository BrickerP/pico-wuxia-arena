"""Independent, offline invariants and dense surface audit for offhand candidates.

Run with Blender --background --python-exit-code 1 --python this_file.
Writes only this directory's audit.json. Public assets remain read-only.
"""

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

import numpy as np
from measure_weapon_surface import measure_left_weapon
from prepare_character_library import decode_animation, sample_track, node_order, sampled_local
from prepare_rigged_warrior import read_glb
from refine_character_grips import accessor


SOURCE_HASHES = {
    "indigo": "4516458ab2d44d986046d36c8349a5901ef20452e60e6570f56c6540d172ee43",
    "veteran": "010e80a08573d0b165692b30a06fcc93f6f0394181fa138b198aa09049b934a3",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    vector = np.array(value, dtype=float)
    require(np.isfinite(vector).all() and np.linalg.norm(vector) > 1e-12, "invalid quaternion")
    return vector / np.linalg.norm(vector)


def multiply(a, b):
    av, bv = np.array(a[:3]), np.array(b[:3])
    return np.concatenate((a[3] * bv + b[3] * av + np.cross(av, bv),
                           [a[3] * b[3] - av @ bv]))


def angle(a, b):
    dot = float(abs(normalized(a) @ normalized(b)))
    return math.degrees(2 * math.acos(min(1.0, dot)))


def weight(time, window):
    start, peak, plateau, end = window
    require(start < peak <= plateau < end, "invalid smooth window")
    if time <= start or time >= end:
        return 0.0
    if time < peak:
        return (1 - math.cos(math.pi * (time - start) / (peak - start))) / 2
    if time <= plateau:
        return 1.0
    return (1 + math.cos(math.pi * (time - plateau) / (end - plateau))) / 2


def delta_between(source_track, candidate_track, time):
    original = normalized(sample_track(source_track, time, True))
    candidate = normalized(sample_track(candidate_track, time, True))
    inverse = np.array([-original[0], -original[1], -original[2], original[3]])
    return normalized(multiply(inverse, candidate))


def verify_invariants(source, old_binary, candidate, binary, config):
    for field in ("nodes", "skins", "meshes", "materials", "images", "textures", "scenes", "scene"):
        require(source.get(field) == candidate.get(field), "preserved field changed: " + field)
    require(len(candidate["skins"][0]["joints"]) == 78, "joint count changed")
    require(binary[:len(old_binary)] == old_binary, "original binary/mesh/skin/weights/binds changed")
    require(candidate["accessors"][:len(source["accessors"])] == source["accessors"], "original accessors changed")
    require(candidate["bufferViews"][:len(source["bufferViews"])] == source["bufferViews"], "original bufferViews changed")
    require(len(source["animations"]) == len(candidate["animations"]) == 8, "clip count changed")
    allowed = set(config["rotations"])
    require(allowed and allowed <= {"L_Hand", "L_Forearm", *[
        "L_" + finger + str(joint) for finger in ("Thumb", "Index", "Mid", "Ring", "Pinky")
        for joint in (1, 2, 3)]}, "rotation scope exceeds offhand")
    changed = []
    for old, new in zip(source["animations"], candidate["animations"]):
        require(old["name"] == new["name"], "clip identity changed")
        if old["name"] != "slash":
            require(old == new, "non-slash clip changed: " + old["name"])
            continue
        require(old["channels"] == new["channels"], "slash channel targets changed")
        require(len(old["samplers"]) == len(new["samplers"]), "slash sampler count changed")
        old_tracks, _ = decode_animation({**source, "animations": [old]}, old_binary)
        new_tracks, _ = decode_animation({**candidate, "animations": [new]}, binary)
        for channel in old["channels"]:
            target = channel["target"]
            bone = source["nodes"][target["node"]].get("name")
            before, after = old["samplers"][channel["sampler"]], new["samplers"][channel["sampler"]]
            permitted = target["path"] == "rotation" and bone in allowed
            if not permitted:
                require(before == after, "non-permitted track changed: " + str(bone))
                continue
            require(before != after, "requested rotation missing: " + bone)
            require(after.get("interpolation", "LINEAR") == before.get("interpolation", "LINEAR") == "LINEAR",
                    "rotation interpolation changed")
            old_times = accessor(source, old_binary, before["input"]).reshape(-1)
            new_times = accessor(candidate, binary, after["input"]).reshape(-1)
            require(set(old_times) <= set(new_times), "original key times removed")
            require(old_times[0] == new_times[0] and old_times[-1] == new_times[-1], "clip time range changed")
            require(np.diff(new_times).min() > 0, "non-increasing key times")
            values = accessor(candidate, binary, after["output"])
            require(np.isfinite(values).all() and np.max(abs(np.linalg.norm(values, axis=1) - 1)) < 1e-5,
                    "candidate quaternion is not finite/unit")
            require(np.min(np.sum(values[:-1] * values[1:], axis=1)) >= -1e-7,
                    "candidate quaternion signs jump between adjacent keys")
            a = old_tracks[(target["node"], "rotation")]
            b = new_tracks[(target["node"], "rotation")]
            rule = config["rotations"][bone]
            axis = np.array(rule["axis"], dtype=float)
            require(np.isfinite(axis).all() and np.linalg.norm(axis) > 1e-12, "invalid correction axis")
            axis /= np.linalg.norm(axis)
            errors, deltas, outside = [], [], []
            for time in new_times:
                half = math.radians(rule["degrees"]) * weight(float(time), config["window_seconds"]) / 2
                expected = np.concatenate((axis * math.sin(half), [math.cos(half)]))
                actual = delta_between(a, b, float(time))
                errors.append(angle(expected, actual))
                deltas.append(angle([0, 0, 0, 1], actual))
                if time <= config["window_seconds"][0] or time >= config["window_seconds"][-1]:
                    outside.append(deltas[-1])
            require(max(errors) < .001, "encoded keys differ from reviewed smooth correction")
            require(max(outside, default=0) < .001, "rotation changed outside reviewed window")
            probes = []
            for seam in config["window_seconds"]:
                qs = [delta_between(a, b, seam + offset) for offset in (-.001, 0, .001)]
                probes.append({"time_seconds": seam,
                    "correction_degrees_before_at_after": [angle([0, 0, 0, 1], q) for q in qs],
                    "one_sided_sampled_correction_speed_degrees_per_second": [angle(qs[0], qs[1]) / .001,
                                                                             angle(qs[1], qs[2]) / .001]})
            changed.append({"bone": bone, "clip": "slash", "source_key_count": len(old_times),
                "candidate_key_count": len(new_times), "maximum_local_correction_degrees": max(deltas),
                "maximum_expected_key_error_degrees": max(errors),
                "maximum_outside_window_correction_degrees": max(outside, default=0), "seams": probes})
    require({row["bone"] for row in changed} == allowed, "wrong changed rotation set")
    require(len(candidate["accessors"]) == len(source["accessors"]) + len(changed) * 2,
            "unexpected appended accessor count")
    require(len(candidate["bufferViews"]) == len(source["bufferViews"]) + len(changed) * 2,
            "unexpected appended view count")
    return {"rest_mesh_weights_inverse_bind_and_original_binary_exact": True,
            "all_other_clips_and_nonpermitted_tracks_exact": True,
            "right_hand_and_dao_channels_exact": True, "changed_rotation_tracks": changed}


def surface_summary(report):
    rows = [value["groups"]["whole_dao"] for value in report["pose_measurements"]]
    return {"sampled_pose_count": len(rows),
            "total_confirmed_triangle_crossing_pairs": sum(row["confirmed_noncoplanar_triangle_crossing_pairs"] for row in rows),
            "maximum_confirmed_triangle_crossing_pairs": max(row["confirmed_noncoplanar_triangle_crossing_pairs"] for row in rows),
            "total_samples_within_3mm": sum(row["samples_within_3mm"] for row in rows),
            "minimum_unsigned_vertex_surface_gap_mm": min(row["minimum_vertex_surface_gap_mm"] for row in rows)}


def left_wrist_motion(source, old_binary, candidate, binary, times):
    samples = []
    for document, packed in ((source, old_binary), (candidate, binary)):
        slash = next(clip for clip in document["animations"] if clip["name"] == "slash")
        tracks, _ = decode_animation({**document, "animations": [slash]}, packed)
        parents, order = node_order(document)
        hand = next(index for index, node in enumerate(document["nodes"]) if node.get("name") == "L_Hand")
        positions = []
        for time in times:
            world = {}
            for index in order:
                local = sampled_local(document["nodes"][index], index, tracks, time)
                world[index] = world[parents[index]] @ local if index in parents else local
            positions.append(np.array(world[hand].translation))
        samples.append(np.array(positions))
    shift = np.linalg.norm(samples[1] - samples[0], axis=1) * 1000
    return {"maximum_left_wrist_world_translation_change_mm": float(shift.max()),
            "maximum_shift_at_seconds": float(times[int(shift.argmax())])}


def audit(config):
    source_path, candidate_path = REPO / config["source"], REPO / config["candidate"]
    old_hash, new_hash = digest(source_path), digest(candidate_path)
    require(old_hash == config["source_sha256"] == SOURCE_HASHES[config["id"]], "reviewed source hash mismatch")
    require(new_hash == config["candidate_sha256"], "candidate hash mismatch")
    source, old_binary = read_glb(source_path)
    candidate, binary = read_glb(candidate_path)
    invariants = verify_invariants(source, old_binary, candidate, binary, config)
    times = {1 + frame / 120 for frame in range(361)} | {1.55, 2.117, 3.4}
    for seam in config["window_seconds"]:
        times.update(seam + offset for offset in (-.001, 0, .001))
    start, peak, _, _ = config["window_seconds"]
    times.update(start + (peak - start) * fraction for fraction in (.25, .5, .75))
    poses = [("slash", time) for time in sorted(times)]
    alignment = json.loads((REPO / "ArtSource/tripo-warrior/library" / (config["id"] + "_alignment.json")).read_text())
    before = measure_left_weapon(source, old_binary, alignment, poses)
    after = measure_left_weapon(candidate, binary, alignment, poses)
    regressions = []
    for old, new in zip(before["pose_measurements"], after["pose_measurements"]):
        a, b = old["groups"]["whole_dao"], new["groups"]["whole_dao"]
        if b["confirmed_noncoplanar_triangle_crossing_pairs"] > a["confirmed_noncoplanar_triangle_crossing_pairs"]:
            regressions.append({"time_seconds": new["time_seconds"], "before": a, "after": b})
    require(old_hash == digest(source_path) and new_hash == digest(candidate_path), "inputs changed during audit")
    reviewed_before = {"pose_measurements": [row for row in before["pose_measurements"] if 1.55 <= row["time_seconds"] <= 3.4]}
    reviewed_after = {"pose_measurements": [row for row in after["pose_measurements"] if 1.55 <= row["time_seconds"] <= 3.4]}
    return {"id": config["id"], "source_sha256": old_hash, "candidate_sha256": new_hash,
            "files_stable_during_audit": True, "invariants": invariants,
            "left_wrist_motion": left_wrist_motion(source, old_binary, candidate, binary, sorted(times)),
            "before_summary": surface_summary(before), "after_summary": surface_summary(after),
            "review_range_1_55_to_3_4_before": surface_summary(reviewed_before),
            "review_range_1_55_to_3_4_after": surface_summary(reviewed_after),
            "all_sampled_surfaces_clear": after["maximum_confirmed_triangle_crossing_pairs"] == 0,
            "crossing_regression_poses": regressions, "before": before, "after": after}


def main():
    config = json.loads((HERE / "calibration.json").read_text())
    result = {"scope": "Independent actual-skinned-mesh 120fps half-step samples over slash 1.0–4.0s plus quarter-rise and window seams +/-1ms; no continuous-clearance or penetration-depth claim",
              "smoothness_scope": "raised-cosine values checked at encoded keys; exported LINEAR sampling is C0 with sampled one-sided slopes, not an exact C1 curve",
              "characters": [], "errors": []}
    for character in config["characters"]:
        try:
            row = audit(character)
            result["characters"].append(row)
            print("OFFHAND_AUDIT", row["id"], json.dumps({"before": row["before_summary"],
                  "after": row["after_summary"], "regressions": len(row["crossing_regression_poses"]),
                  "invariants_passed": True}), flush=True)
        except Exception as error:
            result["errors"].append({"id": character["id"], "error": str(error)})
            print("OFFHAND_AUDIT_ERROR", character["id"], str(error), flush=True)
    (HERE / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    require(not result["errors"], "one or more offhand invariant audits failed")


if __name__ == "__main__":
    main()
