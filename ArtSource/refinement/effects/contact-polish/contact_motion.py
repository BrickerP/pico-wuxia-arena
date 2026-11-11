"""Stateless reference trajectory sampling. Actual event tangent is supplied by Root."""
import math


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(vector):
    if len(vector) != 3 or not all(math.isfinite(v) for v in vector):
        raise ValueError('A finite three-vector is required')
    length = math.hypot(*vector)
    if length <= 1e-10:
        raise ValueError('Direction is unavailable')
    return tuple(v/length for v in vector)


def contact_basis(normal, tangent):
    """Project the real cutting tangent onto the contact plane; no guessed direction."""
    n = unit(normal)
    incoming = unit(tangent)
    projection = dot(incoming, n)
    t = unit(tuple(incoming[i] - projection*n[i] for i in range(3)))
    b = (n[1]*t[2] - n[2]*t[1], n[2]*t[0] - n[0]*t[2], n[0]*t[1] - n[1]*t[0])
    return t, b, n


def interpolate(keys, age):
    if age <= keys[0][0]:
        return keys[0][1]
    for (start, first), (end, last) in zip(keys, keys[1:]):
        if age <= end:
            return first + (last-first)*(age-start)/(end-start)
    return keys[-1][1]


def sample_particle(particle, age, point, normal, tangent, gravity=(0, -9.81, 0)):
    """Point is the Stage anchor, already offset once by Root from the contact surface."""
    if not math.isfinite(age) or age < 0 or age >= particle['lifetime_s']:
        return None
    if len(point) != 3 or len(gravity) != 3 or not all(math.isfinite(v) for v in (*point, *gravity)):
        raise ValueError('Finite Stage point and gravity are required')
    basis = contact_basis(normal, tangent)
    offset = particle['initial_position_local_m']
    velocity = particle['initial_velocity_local_mps']
    displacement = tuple(offset[i] + velocity[i]*age for i in range(3))
    position = tuple(point[axis] + sum(basis[i][axis]*displacement[i] for i in range(3)) +
                     .5*gravity[axis]*age*age for axis in range(3))
    opacity = max(0, min(1, interpolate(particle['opacity_keys'], age)))
    return {'position_stage_m': position, 'opacity': opacity}


def sample_ground_particle(particle, age, anchor, normal, tangent):
    """Keep the dust volume's base above the real, already-offset surface plane."""
    sample = sample_particle(particle, age, anchor, normal, tangent)
    if sample is None:
        return None
    n = unit(normal)
    height = dot(tuple(sample['position_stage_m'][i] - anchor[i] for i in range(3)), n)
    if height < 0:
        sample['position_stage_m'] = tuple(sample['position_stage_m'][i] - height*n[i] for i in range(3))
    return sample
