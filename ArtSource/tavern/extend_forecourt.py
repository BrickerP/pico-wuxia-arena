"""Reuse the tavern's paving module to cover the player's fighting area."""

import itertools
import sys
from pathlib import Path

from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tripo-warrior'))
from prepare_rigged_warrior import read_glb, write_glb, world_matrix


def main():
    document, binary = read_glb(HERE / 'tavern_slice.glb')
    nodes = document['nodes']
    paving = next(index for index, node in enumerate(nodes) if node.get('name') == 'Paving_Root')
    parents = {child:index for index,node in enumerate(nodes) for child in node.get('children', [])}
    bounds = []
    pending = [paving]
    while pending:
        index = pending.pop()
        node = nodes[index]
        pending.extend(node.get('children', []))
        if 'mesh' not in node:
            continue
        transform = world_matrix(nodes, index)
        for primitive in document['meshes'][node['mesh']]['primitives']:
            position = document['accessors'][primitive['attributes']['POSITION']]
            for corner in itertools.product(*zip(position['min'], position['max'])):
                bounds.append(transform @ Vector(corner))
    depth = max(point.z for point in bounds) - min(point.z for point in bounds)
    current = paving
    while current in parents:
        parent = parents[current]
        nodes[parent]['children'] = [current]
        current = parent
    root = len(nodes)
    nodes.append({'name':'Forecourt_Root', 'translation':[0,0,depth], 'children':[current]})
    document['scenes'] = [{'name':'Forecourt', 'nodes':[root]}]
    document['scene'] = 0
    output = write_glb(HERE / 'forecourt.glb', document, binary)
    print(output)


if __name__ == '__main__':
    main()
