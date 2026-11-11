"""Generate Kotlin attack data from the final prepared actors; never writes model assets."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_BANK = REPO / 'ArtSource/tripo-warrior/library'
DEFAULT_OUTPUT = REPO / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/AttackBankProfileData.kt'
DIRECTIONS = ('OVERHEAD', 'LEFT', 'RIGHT')
FIELDS = ('head', 'body_bottom', 'body_top', 'blade_base', 'blade_tip')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gait_step_events(profile):
    contract = profile['source_contract']
    if (contract.get('contract') != 'locomotion78' or contract['stride_metres'] != 1.45 or
            contract['steps_per_loop'] != 6 or contract['loop_start_seconds'] != 1 / 3 or
            contract['loop_end_seconds'] != 1.5):
        raise ValueError('Expected the frozen six-step locomotion78 clock')
    start, end = contract['loop_start_seconds'], contract['loop_end_seconds']
    contacts = contract['contact_phases']
    if set(contacts) != {'L_', 'R_'} or any(len(v) != 3 for v in contacts.values()):
        raise ValueError('Six-step contact phases require three stance intervals per foot')
    entries = sorted((interval[0], side) for side, intervals in contacts.items() for interval in intervals)
    events = []
    for index, (time, side) in enumerate(entries):
        phase = (time - start) / (end - start)
        wanted = 'L_' if index % 2 == 0 else 'R_'
        if not math.isfinite(phase) or abs(phase - index / 6) > 1e-9 or side != wanted:
            raise ValueError('Six-step support entry phases or feet differ from the frozen clock')
        forward = 'LEFT' if side == 'L_' else 'RIGHT'
        events.append((phase, forward, 'RIGHT' if forward == 'LEFT' else 'LEFT'))
    return events


def validate_pose_samples(samples, start, end):
    previous = -math.inf
    for sample in samples:
        time = sample['source_seconds']
        if not math.isfinite(time) or time <= previous:
            raise ValueError('Samples must have finite increasing source times')
        previous = time
        for field in FIELDS:
            if len(sample[field]) != 3 or not all(math.isfinite(v) for v in sample[field]):
                raise ValueError('Invalid anchor: ' + field)
    if not samples or samples[0]['source_seconds'] != start or samples[-1]['source_seconds'] != end:
        raise ValueError('Pose samples must include their exact source endpoints')


def sampled_fields(samples, time):
    index = bisect.bisect_left([sample['source_seconds'] for sample in samples], time)
    if index == 0:
        return {field: samples[0][field] for field in FIELDS}
    if index == len(samples):
        return {field: samples[-1][field] for field in FIELDS}
    before, after = samples[index - 1], samples[index]
    alpha = (time - before['source_seconds']) / (after['source_seconds'] - before['source_seconds'])
    return {field: [a * (1 - alpha) + b * alpha for a, b in zip(before[field], after[field])] for field in FIELDS}


def validate_canonical_boundaries(profile):
    idle = profile['locomotion']['idle']['samples'][0]
    walk = sampled_fields(profile['locomotion']['walk']['samples'], profile['source_contract']['loop_start_seconds'])
    if any(walk[field] != idle[field] for field in FIELDS):
        raise ValueError('Final idle and walk canonical boundary anchors differ')
    # Retargeted float32 attack entries can differ by sub-micrometre rounding only.
    for attack in profile['attacks'].values():
        for sample in [attack['samples'][0], attack['samples'][-1]]:
            if any(math.dist(sample[field], idle[field]) > 1e-6 for field in FIELDS):
                raise ValueError('Final attack canonical boundary anchors drift from idle')


def load_bank(bank):
    review = json.loads((bank / 'production_review_request.json').read_text())
    binding_sha = hashlib.sha256(json.dumps(review['binding'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    if binding_sha != review['binding_sha256']:
        raise ValueError('Prepared library binding identity differs from its review request')
    reviewed = {c['id']: c for c in review['characters']}
    characters = json.loads((bank / 'characters.json').read_text())['characters']
    if [c['id'] for c in characters] != ['base', 'indigo', 'veteran']:
        raise ValueError('Expected the three current arena opponents in round order')
    result = []
    for character in characters:
        profile_file = bank / character['attack_profiles']['file']
        profile_sha = sha256(profile_file)
        if profile_sha != character['attack_profiles']['sha256']:
            raise ValueError('Profile SHA differs from library manifest: ' + character['id'])
        if profile_sha != reviewed[character['id']]['attack_profiles_sha256']:
            raise ValueError('Profile differs from reviewed bank binding')
        profile = json.loads(profile_file.read_text())
        model_sha = sha256(bank / character['output'])
        model_record = next(output for output in character['outputs'] if output['file'] == character['output'])
        reviewed_model = next(output for output in reviewed[character['id']]['outputs'] if output['file'] == character['output'])
        if not model_sha == profile['model_sha256'] == model_record['sha256'] == reviewed_model['sha256']:
            raise ValueError('Prepared model identity differs from its profile/library/review: ' + character['id'])
        if (profile['schema_version'] != 3 or profile['units'] != 'metres' or
                profile['space'] != 'prepared actor root' or
                profile['axes'] != {'up': '+Y', 'forward': '+Z', 'actor_left': '+X'}):
            raise ValueError('Unsupported prepared actor profile contract')
        if review['binding'].get('schema_version') != 3:
            raise ValueError('The canonical bank requires manifest schema 3')
        if set(profile['locomotion']) != {'idle', 'walk'}:
            raise ValueError('The canonical bank requires actual idle and walk profiles')
        gait_step_events(profile)
        for name, clip in profile['locomotion'].items():
            if (clip['clip'] != name or clip['source_range_seconds'] != [0, 1.5] or
                    clip['source_loop_seconds'] != [1 / 3, 1.5] or
                    clip['animation_semantics_sha256'] != reviewed[character['id']]['clip_semantic_signatures'][name]):
                raise ValueError('Locomotion clip identity/timing differs from the reviewed model')
            validate_pose_samples(clip['samples'], 0.0, 1.5)
        if set(profile['attacks']) != set(DIRECTIONS):
            raise ValueError('Exactly three attack directions are required')
        for direction in DIRECTIONS:
            attack = profile['attacks'][direction]
            if attack['animation_semantics_sha256'] != reviewed[character['id']]['clip_semantic_signatures'][attack['clip']]:
                raise ValueError('Attack curve identity differs from reviewed prepared model')
            if attack['clip'] != 'attack_' + direction.lower():
                raise ValueError('Direction/clip mismatch')
            if profile['directions'][direction]['incoming_guard_side'] != direction:
                raise ValueError('Direction must use player-view incoming side')
            phases = attack['source_phase_seconds']
            contact = attack['contact_source_seconds']
            if phases != [0, .65, .90, 1.10, 1.75] or contact != 1.0:
                raise ValueError('Unexpected source phase/contact markers')
            previous = -math.inf
            for sample in attack['samples']:
                time = sample['source_seconds']
                if not math.isfinite(time) or time <= previous:
                    raise ValueError('Samples must have finite increasing source times')
                previous = time
                for field in FIELDS:
                    if len(sample[field]) != 3 or not all(math.isfinite(v) for v in sample[field]):
                        raise ValueError('Invalid anchor: ' + field)
            if (attack['samples'][0]['source_seconds'] != phases[0] or
                    attack['samples'][-1]['source_seconds'] != phases[-1] or
                    not any(s['source_seconds'] == contact for s in attack['samples'])):
                raise ValueError('Samples must include source endpoints and the exact contact key')
        validate_canonical_boundaries(profile)
        result.append((character, profile, profile_sha))
    return result


def kotlin_double(value):
    result = format(value, '.17g')
    return result if any(c in result for c in '.eE') else result + '.0'


def generate(bank):
    loaded = load_bank(bank)
    binding_sha = json.loads((bank / 'production_review_request.json').read_text())['binding_sha256']
    lines = [
        '// Generated by ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py.',
        '// Regenerate together with the matching prepared GLBs; do not hand-edit anchors.',
        f'// Prepared source: {bank.resolve().relative_to(REPO).as_posix()}',
        'package com.example.wuxiaarena.p0d2f0182.runtime', '',
        'import com.example.wuxiaarena.core.combat.AttackDirection',
        'import com.example.wuxiaarena.core.combat.EnemyContactPose',
        'import com.example.wuxiaarena.core.math.Vector3', '',
        'internal object AttackBankProfileData {',
        f'    const val bindingSha256 = "{binding_sha}"',
        '    val characters: Map<String, CharacterAttackProfiles> = mapOf(',
    ]
    for character, profile, profile_sha in loaded:
        cid = character['id']
        lines += [
            f'        "asset://models/opponents/{cid}.glb" to CharacterAttackProfiles(',
            f'            modelSha256 = "{profile["model_sha256"]}",',
            f'            profileSha256 = "{profile_sha}",',
            '            attacks = mapOf(',
        ]
        for direction in DIRECTIONS:
            attack = profile['attacks'][direction]
            phases = ', '.join(str(float(v)) for v in attack['source_phase_seconds'])
            lines += [
                f'                // Animation semantics SHA-256 {attack["animation_semantics_sha256"]}',
                f'                AttackDirection.{direction} to AttackProfile(',
                f'                    clip = "{attack["clip"]}",',
                f'                    sourcePhaseSeconds = listOf({phases}),',
                f'                    contactSourceSeconds = {float(attack["contact_source_seconds"])},',
                f'                    samples = {cid}{direction.title()}(),',
                '                ),',
            ]
        lines += ['            ),', '            locomotion = LocomotionProfile(',
                  f'                idle = PoseClipProfile("idle", {cid}Idle()),',
                  f'                walk = PoseClipProfile("walk", {cid}Walk()),',
                  f'                loopStartSeconds = {kotlin_double(profile["source_contract"]["loop_start_seconds"])},',
                  f'                loopEndSeconds = {kotlin_double(profile["source_contract"]["loop_end_seconds"])},',
                  f'                strideMeters = {kotlin_double(profile["source_contract"]["stride_metres"])},',
                  '                stepEvents = listOf(']
        for phase, forward, reverse in gait_step_events(profile):
            lines.append(f'                    GaitStepEvent({kotlin_double(phase)}, EnemyFoot.{forward}, EnemyFoot.{reverse}),')
        lines += ['                ),', '            ),', '        ),']
    lines += ['    )', '}', '',
              '// Columns: source seconds, head xyz, lower torso xyz, upper torso xyz, blade base xyz, blade tip xyz.',
              'private fun decodeAttackSamples(values: DoubleArray): List<AttackPoseSample> {',
              '    check(values.size % 16 == 0) { "Attack samples require time and five anchors" }',
              '    fun vector(index: Int) = Vector3(values[index], values[index + 1], values[index + 2])',
              '    return (values.indices step 16).map { offset ->',
              '        AttackPoseSample(values[offset], EnemyContactPose(vector(offset + 1), vector(offset + 4), vector(offset + 7)),',
              '            vector(offset + 10), vector(offset + 13))',
              '    }', '}', '']
    for character, profile, _ in loaded:
        clips = [(direction.title(), profile['attacks'][direction]) for direction in DIRECTIONS]
        clips += [(name.title(), clip) for name, clip in profile['locomotion'].items()]
        for title, clip in clips:
            lines.append(f'private fun {character["id"]}{title}(): List<AttackPoseSample> = decodeAttackSamples(doubleArrayOf(')
            for sample in clip['samples']:
                values = [sample['source_seconds'], *[v for field in FIELDS for v in sample[field]]]
                lines.append('    ' + ', '.join(kotlin_double(v) for v in values) + ',')
            lines += ['))', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, default=DEFAULT_BANK)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = generate(args.bank)
    if args.check:
        if args.output.read_text() != content:
            raise SystemExit('Generated Kotlin attack bank differs from the prepared library')
        print('Verified exact generated attack data: 3 actors × 3 attacks + actual idle/walk')
    else:
        args.output.write_text(content)
        print(f'Generated {args.output.relative_to(REPO)} ({len(content)} characters)')


if __name__ == '__main__':
    main()
