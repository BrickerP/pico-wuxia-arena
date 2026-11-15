"""Generate Kotlin attack data from the final prepared actors; never writes model assets."""
import argparse
import bisect
import hashlib
import json
import math
import sys
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'ArtSource/tripo-warrior'))
from production_contract import canonical_hash, production_binding
DEFAULT_BANK = REPO / 'ArtSource/tripo-warrior/library'
DEFAULT_OUTPUT = REPO / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/AttackBankProfileData.kt'
ENEMY_COMBAT_SOURCE = REPO / 'app/src/main/java/com/example/wuxiaarena/core/combat/EnemyCombatStateMachine.kt'
DIRECTIONS = ('OVERHEAD', 'LEFT', 'RIGHT')
PHASE_MARKERS = ('start', 'preparation_end', 'startup_end', 'active_end', 'recovery_end', 'contact')
FIELDS = ('head', 'body_bottom', 'body_top', 'blade_base', 'blade_tip')
REACTIONS = {'hit_body': ('body', .72), 'hit_head': ('head', .72), 'hit_side': ('side', 1.18)}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_runtime_phase_nanos(values):
    if (not isinstance(values, list) or len(values) != 4 or
            any(type(value) is not int or not 0 < value <= 2**63 - 1 for value in values)):
        raise ValueError('Runtime phases require four positive integer Long nanosecond durations')
    return values


def runtime_phase_nanos_from_enum():
    """Read the actual four duration literals, rather than maintaining a Python copy."""
    source = ENEMY_COMBAT_SOURCE.read_text()
    source = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.DOTALL)
    declaration = re.search(r'\benum\s+class\s+AttackDirection\s*\([^)]*\)\s*\{(.*?)\}', source, re.DOTALL)
    if declaration is None:
        raise ValueError('AttackDirection enum with explicit runtime durations is absent')
    body = declaration.group(1)
    rows = list(re.finditer(r'([A-Z][A-Z_]*)\s*\(([^()]*)\)\s*(?:,|;|$)', body, re.DOTALL))
    cursor = 0
    result = {}
    literals = r'\s*([0-9][0-9_]*L)\s*,\s*([0-9][0-9_]*L)\s*,\s*([0-9][0-9_]*L)\s*,\s*([0-9][0-9_]*L)\s*,?\s*'
    for row in rows:
        if body[cursor:row.start()].strip() or row.group(1) in result:
            raise ValueError('AttackDirection must declare each direction once with four Long literals')
        match = re.fullmatch(literals, row.group(2))
        if match is None:
            raise ValueError('AttackDirection runtime durations must be four explicit Long literals')
        result[row.group(1)] = validate_runtime_phase_nanos([int(value[:-1].replace('_', '')) for value in match.groups()])
        cursor = row.end()
    if body[cursor:].strip() or set(result) != set(DIRECTIONS):
        raise ValueError('AttackDirection must declare exactly OVERHEAD, LEFT and RIGHT')
    return result


def validate_attack_contracts(binding):
    attacks = binding.get('attack_source')
    if not isinstance(attacks, dict) or 'phase_markers' in attacks:
        raise ValueError('Reviewed attacks require per-direction phase contracts; shared phase_markers are retired')
    clips = attacks.get('clips')
    if (not isinstance(clips, list) or len(clips) != len(DIRECTIONS) or
            any(not isinstance(row, dict) for row in clips) or
            {row.get('direction') for row in clips} != set(DIRECTIONS)):
        raise ValueError('Reviewed attacks require exactly three direction-specific rows')
    runtime = runtime_phase_nanos_from_enum()
    result = {}
    for row in clips:
        direction = row['direction']
        if (row.get('name') != 'attack_' + direction.lower() or row.get('incoming_guard_side') != direction or
                row.get('actor_travel_side') not in {'DOWN', 'LEFT', 'RIGHT'}):
            raise ValueError('Reviewed attack clip and incoming side differ from direction: ' + direction)
        source_sha = row.get('source_sha256')
        if not isinstance(source_sha, str) or re.fullmatch(r'[0-9a-f]{64}', source_sha) is None:
            raise ValueError('Reviewed attack source requires a SHA-256 identity: ' + direction)
        markers = row.get('phase_markers')
        if (not isinstance(markers, dict) or set(markers) != set(PHASE_MARKERS) or
                any(type(value) not in (int, float) or not math.isfinite(value) for value in markers.values())):
            raise ValueError('Reviewed attack requires its six finite phase markers: ' + direction)
        phases = [markers[key] for key in PHASE_MARKERS[:5]]
        if (phases[0] != 0.0 or phases[-1] != 1.75 or
                any(before >= after for before, after in zip(phases, phases[1:])) or
                not phases[2] < markers['contact'] < phases[3]):
            raise ValueError('Reviewed attack phase/contact order differs from the 0..1.75s contract: ' + direction)
        durations = validate_runtime_phase_nanos(row.get('runtime_phase_nanos'))
        if durations != runtime[direction]:
            raise ValueError('Reviewed runtime phases differ from the actual AttackDirection enum: ' + direction)
        result[direction] = row
    return result


def validate_attack_profile(attack, metadata, contract):
    direction = contract['direction']
    if (attack.get('clip') != contract['name'] or metadata.get('incoming_guard_side') != contract['incoming_guard_side'] or
            metadata.get('actor_travel_side') != contract.get('actor_travel_side') or
            metadata.get('source_sha256') != contract['source_sha256']):
        raise ValueError('Attack source/clip/direction differs from the reviewed binding: ' + direction)
    markers = contract['phase_markers']
    phases = [markers[key] for key in PHASE_MARKERS[:5]]
    source_range = attack.get('source_range_seconds')
    source_phases = attack.get('source_phase_seconds')
    contact = attack.get('contact_source_seconds')
    if (not isinstance(source_range, list) or len(source_range) != 2 or
            not isinstance(source_phases, list) or len(source_phases) != 5 or
            any(type(value) not in (int, float) or not math.isfinite(value) for value in [*source_range, *source_phases]) or
            type(contact) not in (int, float) or not math.isfinite(contact)):
        raise ValueError('Attack source phase/contact markers require finite numeric values: ' + direction)
    if (source_range != [phases[0], phases[-1]] or source_phases != phases or contact != markers['contact']):
        raise ValueError('Attack source phase/contact markers differ from its reviewed direction: ' + direction)
    if validate_runtime_phase_nanos(attack.get('runtime_phase_nanos')) != contract['runtime_phase_nanos']:
        raise ValueError('Attack runtime phases differ from its reviewed direction: ' + direction)
    samples = attack.get('samples')
    validate_pose_samples(samples, phases[0], phases[-1])


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
    if not isinstance(samples, list):
        raise ValueError('Pose samples must be a list')
    previous = -math.inf
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError('Pose sample must contain a source time and anchors')
        time = sample.get('source_seconds')
        if type(time) not in (int, float) or not math.isfinite(time) or time <= previous:
            raise ValueError('Samples must have finite increasing source times')
        previous = time
        for field in FIELDS:
            point = sample.get(field)
            if (not isinstance(point, list) or len(point) != 3 or
                    not all(type(v) in (int, float) and math.isfinite(v) for v in point)):
                raise ValueError('Invalid anchor: ' + field)
    if not samples or samples[0]['source_seconds'] != start or samples[-1]['source_seconds'] != end:
        raise ValueError('Pose samples must include their exact source endpoints')


def validate_reactions(profile, reviewed):
    reactions = profile.get('reactions')
    if not isinstance(reactions, dict) or set(reactions) != set(REACTIONS):
        raise ValueError('The canonical bank requires actual hit_body, hit_head and hit_side profiles')
    signatures = reviewed.get('clip_semantic_signatures', {})
    for name, (_, end) in REACTIONS.items():
        clip = reactions[name]
        if not isinstance(clip, dict) or clip.get('clip') != name:
            raise ValueError('Reaction clip identity differs from its profile key')
        signature = signatures.get(name)
        if not signature or clip.get('animation_semantics_sha256') != signature:
            raise ValueError('Reaction curve identity differs from reviewed prepared model: ' + name)
        source = clip.get('source_range_seconds')
        if (not isinstance(source, list) or len(source) != 2 or
                not all(type(v) in (int, float) and math.isfinite(v) and v >= 0.0 for v in source) or
                source[0] >= source[1]):
            raise ValueError('Reaction source range must be finite, non-negative and increasing: ' + name)
        if clip.get('playback_range_seconds') != [.05, end]:
            raise ValueError('Reaction playback range differs from the existing HIT clock: ' + name)
        if source[0] > .05 or source[1] < end:
            raise ValueError('Reaction source range does not cover the complete HIT playback: ' + name)
        validate_pose_samples(clip.get('samples'), *source)


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


def load_bank(bank, review=None):
    if review is None:
        review = json.loads((bank / 'production_review_request.json').read_text())
    binding_sha = hashlib.sha256(json.dumps(review['binding'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    if binding_sha != review['binding_sha256']:
        raise ValueError('Prepared library binding identity differs from its review request')
    contracts = validate_attack_contracts(review['binding'])
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
        if {'phase_markers_seconds', 'phase_sample_times_seconds'}.intersection(profile):
            raise ValueError('Shared profile phase metadata is retired; require per-direction attack phases')
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
        validate_reactions(profile, reviewed[character['id']])
        if set(profile['attacks']) != set(DIRECTIONS):
            raise ValueError('Exactly three attack directions are required')
        if set(profile['directions']) != set(DIRECTIONS):
            raise ValueError('Exactly three source direction identities are required')
        for direction in DIRECTIONS:
            attack = profile['attacks'][direction]
            if attack['animation_semantics_sha256'] != reviewed[character['id']]['clip_semantic_signatures'][attack['clip']]:
                raise ValueError('Attack curve identity differs from reviewed prepared model')
            validate_attack_profile(attack, profile['directions'][direction], contracts[direction])
        validate_canonical_boundaries(profile)
        result.append((character, profile, profile_sha))
    return result


def kotlin_double(value):
    result = format(value, '.17g')
    return result if any(c in result for c in '.eE') else result + '.0'


def generate(bank, review=None):
    if review is None:
        review = json.loads((bank / 'production_review_request.json').read_text())
    loaded = load_bank(bank, review)
    binding_sha = review['binding_sha256']
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
        lines += ['                ),', '            ),', '            reactions = ReactionProfiles(']
        for name, (field, _) in REACTIONS.items():
            clip = profile['reactions'][name]
            title = name.title().replace('_', '')
            lines += [f'                // Animation semantics SHA-256 {clip["animation_semantics_sha256"]}',
                      f'                {field} = PoseClipProfile("{name}", {cid}{title}()),']
        lines += ['            ),', '        ),']
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
        clips += [(name.title().replace('_', ''), profile['reactions'][name]) for name in REACTIONS]
        for title, clip in clips:
            lines.append(f'private fun {character["id"]}{title}(): List<AttackPoseSample> = decodeAttackSamples(doubleArrayOf(')
            for sample in clip['samples']:
                values = [sample['source_seconds'], *[v for field in FIELDS for v in sample[field]]]
                lines.append('    ' + ', '.join(kotlin_double(v) for v in values) + ',')
            lines += ['))', '']
    return '\n'.join(lines)


def validate_app_publication(manifest_path, request):
    """Use the producer's existing Root receipt; a request status alone cannot approve."""
    if request.get('status') != 'approved_for_development_integration':
        raise ValueError('App publication requires approved_for_development_integration bank status')
    manifest = json.loads(manifest_path.read_text())
    try:
        current_binding = json.loads(json.dumps(production_binding(manifest)))
    except (KeyError, TypeError) as error:
        raise ValueError('Current manifest lacks complete production binding inputs') from error
    if (current_binding != request.get('binding') or
            canonical_hash(current_binding) != request.get('binding_sha256')):
        raise ValueError('Current manifest production binding differs from the reviewed bank')
    entry = manifest.get('production_review')
    if not entry:
        raise ValueError('App publication requires Root production_review after candidate inspection')
    # Match prepare_character_library.HERE even when --manifest lives elsewhere.
    review_path = REPO / 'ArtSource/tripo-warrior' / entry['source']
    if sha256(review_path) != entry['source_sha256']:
        raise ValueError('Production review file hash changed')
    review = json.loads(review_path.read_text())
    if review.get('decision') != 'approved' or review.get('binding_sha256') != request['binding_sha256']:
        raise ValueError('Production review does not approve the current sources and hand policy')
    if review.get('characters') != request['characters']:
        raise ValueError('Production review differs from final outputs, hand tracks or attack profiles')
    if review.get('player_weapon') != request.get('player_weapon'):
        raise ValueError('Production review differs from the encoded player weapon')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, default=DEFAULT_BANK)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--manifest', type=Path, default=REPO / 'ArtSource/tripo-warrior/motion_library.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    destination = args.output.resolve()
    app = (REPO / 'app').resolve()
    request = json.loads((args.bank / 'production_review_request.json').read_text())
    if not args.check and (destination == app or app in destination.parents):
        validate_app_publication(args.manifest, request)
    content = generate(args.bank, request)
    if args.check:
        if destination.read_text() != content:
            raise SystemExit('Generated Kotlin attack bank differs from the prepared library')
        print('Verified exact generated attack data: 3 actors × 3 attacks + actual idle/walk and HIT reactions')
    else:
        destination.write_text(content)
        print(f'Generated {args.output} ({len(content)} characters)')


if __name__ == '__main__':
    main()
