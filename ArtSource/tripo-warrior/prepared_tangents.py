"""One pinned, append-only prepared PNG tangent stage before runtime encoding."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


STAGE = 'prepared_png_after_wrist_before_texture_v1'
TOOL_FILES = {
    'build_tangents.mjs', 'glb_io.mjs', 'mikktspace.mjs',
    'geometry_contract.json', 'degenerate_policy.json',
    'licenses/MikkTSpace-original-zlib-notice.txt',
    'licenses/mikktspace-wasm-MIT.txt', 'licenses/three-MIT.txt',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_prepared_tangents(manifest, source_root):
    config = manifest.get('prepared_tangents')
    if (not isinstance(config, dict) or
            set(config) != {'stage', 'targets', 'implementation', 'tools', 'host_node'} or
            config['stage'] != STAGE or config['targets'] != ['veteran']):
        raise ValueError('the current bank requires the reviewed veteran prepared tangent stage')
    if 'veteran' not in {row['id'] for row in manifest['characters']}:
        raise ValueError('prepared tangent target is absent from the character bank')
    if not isinstance(config['tools'], dict) or set(config['tools']) != TOOL_FILES:
        raise ValueError('prepared tangent tool closure is incomplete')
    source_root = Path(source_root).resolve()
    repo = source_root.parent.parent
    implementation = config['implementation']
    if (not isinstance(implementation, dict) or
            set(implementation) != {'source', 'source_sha256'}):
        raise ValueError('prepared tangent orchestration identity is required')
    implementation_path = (source_root / implementation['source']).resolve()
    if (not implementation_path.is_relative_to(repo) or
            implementation_path != Path(__file__).resolve() or
            digest(implementation_path) != implementation['source_sha256']):
        raise ValueError('prepared tangent orchestration identity changed')
    tool_parent = None
    for name, entry in config['tools'].items():
        if not isinstance(entry, dict) or set(entry) != {'source', 'source_sha256'}:
            raise ValueError('invalid prepared tangent tool identity: ' + name)
        path = (source_root / entry['source']).resolve()
        if not path.is_relative_to(repo):
            raise ValueError('prepared tangent tool escapes the repository: ' + name)
        if digest(path) != entry['source_sha256']:
            raise ValueError('prepared tangent tool identity changed: ' + name)
        # The CLI resolves sibling imports and its frozen contracts here.
        parent = path
        for unused in Path(name).parts:
            parent = parent.parent
        if tool_parent is None:
            tool_parent = parent
        elif tool_parent != parent:
            raise ValueError('prepared tangent tools must have one self-contained directory')
        if path.relative_to(parent).as_posix() != name:
            raise ValueError('prepared tangent tool filename differs from its declared role')
    node = config['host_node']
    if (not isinstance(node, dict) or set(node) != {'source', 'source_sha256', 'version'} or
            digest(source_root / node['source']) != node['source_sha256']):
        raise ValueError('prepared tangent host Node identity changed')
    actual = subprocess.run([str(source_root / node['source']), '--version'],
                            text=True, capture_output=True, check=True, timeout=10)
    if actual.stdout.strip() != node['version']:
        raise ValueError('prepared tangent host Node version changed')
    return config


def apply_prepared_tangents(character_id, source, config, source_root):
    if character_id not in config['targets']:
        return {'applied': False}
    source = Path(source)
    before = digest(source)
    source_root = Path(source_root)
    node = source_root / config['host_node']['source']
    tool = source_root / config['tools']['build_tangents.mjs']['source']
    # Only source contents establish whether this stage already ran. A unique
    # same-filesystem workspace permits canonical rebuilds at the same path and
    # makes publication atomic without depending on adjacent stale diagnostics.
    with tempfile.TemporaryDirectory(prefix='.' + source.stem + '-tangent-',
                                     dir=source.parent) as temporary:
        workspace = Path(temporary)
        output, report_dir = workspace / 'model.glb', workspace / 'review'
        result = subprocess.run([str(node), str(tool), str(source), str(output), str(report_dir)],
                                text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise ValueError('prepared tangent stage failed:\n' + result.stdout + '\n' + result.stderr)
        report = json.loads((report_dir / 'generation.json').read_text())
        if (digest(source) != before or report.get('status') != 'PASS' or
                report['input']['sha256'] != before or
                report['output']['sha256'] != digest(output) or
                report.get('preservation', {}).get('pass') is not True or
                [row.get('primitive') for row in report['primitives']] != [0, 1, 2, 3, 4] or
                not all(row.get('pass') is True for row in report['primitives'])):
            raise ValueError('prepared tangent output does not match its preservation report')
        # Retain the complete generation report in the production record/request,
        # using stable published names rather than a removed temporary path.
        report['input']['file'] = source.name
        report['output']['file'] = source.name
        report['generator'].pop('existing_module_read_only', None)
        report['generator']['module'] = config['tools']['mikktspace.mjs']
        output.replace(source)
        return {'applied': True, 'stage': STAGE, **report}
