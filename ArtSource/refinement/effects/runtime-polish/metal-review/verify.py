"""Check the actual nine-frame calibration output and unchanged comparison inputs."""
import json
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
CONTACT = HERE.parents[1] / 'contact-polish'
sys.path.insert(0, str(CONTACT))
from contact_motion import interpolate
manifest = json.loads((HERE / 'render_manifest.json').read_text())
before = json.loads((HERE / 'calibration-before/render_manifest.json').read_text())
assert len(manifest['images']) == 9
for name in manifest['images']:
    with Image.open(HERE / name) as image:
        assert image.size == (800, 600)
        image.verify()
assert manifest['opacity_ownership']['object_count'] == 29 == manifest['opacity_ownership']['distinct_material_count']
comparison_keys = ['actor_sha256', 'baseline_sha256', 'candidate_sha256', 'motion_sha256',
                   'contact_point_blender_m', 'actual_surface_normal_blender', 'distance_m',
                   'horizontal_fov_degrees', 'basis_stage', 'stage_gravity_mps2',
                   'normal_particle_scale', 'parry_particle_scale', 'parry_velocity_extra', 'core_seconds']
assert all(manifest[key] == before[key] for key in comparison_keys)
assert manifest['normal_core_scale'] == '(.85 + min(age,.09)*3)*1.019*1.9'
assert manifest['parry_core_scale'] == '(.85 + min(age,.09)*3)*1.019*2.6'
assert not manifest['scale_gravity']
motion = json.loads((CONTACT / 'metal/motion.json').read_text())
core = motion['cores'][0]
opacity = {}
diameters = {}
for label, age in [('33ms', 1/30), ('67ms', 2/30), ('167ms', 5/30)]:
    opacity[label] = {kind: interpolate(core[kind]['opacity_keys'], age) if age < core[kind]['lifetime_s'] else 0 for kind in ('normal', 'parry')}
    diameters[label] = {kind: core['diameter_m'] * (.85 + min(age, .09) * 3) * 1.019 * gain if age < core[kind]['lifetime_s'] else 0 for kind, gain in [('normal', 1.9), ('parry', 2.6)]}
assert opacity['67ms']['normal'] == 0 and opacity['67ms']['parry'] > 0
assert opacity['167ms']['normal'] == 0 and opacity['167ms']['parry'] == 0
result = {'images_verified': 9, 'frame_size': [800, 600], 'distinct_opacity_materials': 29,
          'unchanged_before_after_input_keys': comparison_keys, 'only_parameter_change': 'Core multiplier ordinary 1.9 / parry 2.6',
          'core_opacity_at_samples': opacity, 'core_diameter_m_at_samples': diameters,
          'previous_calibration': 'calibration-before/; early ordinary metal readability did not pass',
          'scope': 'Actual offline frames and stateless timing/numeric verification; not SDK/Space Pro acceptance'}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
