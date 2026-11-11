"""Public Blender object-slot opacity ownership matching per-Entity runtime opacity.

MaterialSlot.link/material and ID.copy were checked through Blender 4.5 RNA help.
Object-level slots avoid altering any other object sharing the same mesh data.
"""
LABEL = 'OfflineParticleOpacity'


def independent_alpha_controls(obj):
    controls = []
    for slot in obj.material_slots:
        original = slot.material
        if original is None:
            raise ValueError(f'Missing particle material on {obj.name}')
        if any(node.label == LABEL for node in original.node_tree.nodes):
            raise ValueError(f'Opacity already configured for {obj.name}')
        material = original.copy()
        slot.link = 'OBJECT'
        slot.material = material
        if material.users != 1:
            raise ValueError(f'Particle material is still shared on {obj.name}')
        shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        target = shader.inputs['Alpha']
        multiplier = material.node_tree.nodes.new('ShaderNodeMath')
        multiplier.operation = 'MULTIPLY'
        multiplier.label = LABEL
        if target.is_linked:
            link = target.links[0]
            original_alpha = link.from_socket
            material.node_tree.links.remove(link)
            material.node_tree.links.new(original_alpha, multiplier.inputs[0])
        else:
            multiplier.inputs[0].default_value = target.default_value
        multiplier.inputs[1].default_value = 1
        material.node_tree.links.new(multiplier.outputs[0], target)
        controls.append(multiplier.inputs[1])
    return controls


def ownership_report(objects):
    slots = []
    for obj in objects:
        for slot in obj.material_slots:
            material = slot.material
            count = sum(node.label == LABEL for node in material.node_tree.nodes)
            if slot.link != 'OBJECT' or material.users != 1 or count != 1:
                raise ValueError(f'Independent alpha contract failed for {obj.name}')
            slots.append({'object': obj.name, 'mesh_identity': obj.data.as_pointer(),
                          'material_identity': material.as_pointer(), 'material_users': material.users,
                          'slot_link': slot.link, 'independent_alpha_multiplier_count': count})
    identities = {slot['material_identity'] for slot in slots}
    if len(identities) != len(slots):
        raise ValueError('Two particle slots still share a material')
    return {'object_count': len(objects), 'slot_count': len(slots),
            'distinct_material_count': len(identities), 'slots': slots,
            'semantics': 'Each object uses its own material and one factor; no per-particle alpha product'}
