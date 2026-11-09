"""Build the modular tavern entrance and offline review images in Blender 4.5.

Only the named asset roots are exported. The studio and its lights are not
game assets. See README.md for the two CC0 texture sources and rebuild steps.
"""

import math
import random
from array import array
from pathlib import Path

import bpy
from mathutils import Vector


OUT = Path(__file__).resolve().parent
TEXTURES = OUT / "textures"
random.seed(739)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

asset = bpy.data.collections.new("TAVERN_ASSET")
scene.collection.children.link(asset)
studio = bpy.data.collections.new("REVIEW_STUDIO")
scene.collection.children.link(studio)


def solid(name, color, roughness=.7, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def wet_roughness(source_file, output_file, seed, wet_amount):
    """Make a tileable, spatially uneven wet roughness map from the CC0 scan."""
    source = bpy.data.images.load(str(TEXTURES / source_file), check_existing=True)
    source.colorspace_settings.name = "Non-Color"
    width, height = source.size
    source_pixels = array("f", [0.0]) * (width * height * 4)
    source.pixels.foreach_get(source_pixels)
    rng = random.Random(seed)
    size = 12
    grid = [[rng.random() for _ in range(size)] for _ in range(size)]
    result = array("f")
    for py in range(height):
        gy = py / height * size
        iy, fy = int(gy), gy % 1
        for px in range(width):
            gx = px / width * size
            ix, fx = int(gx), gx % 1
            a = grid[iy][ix]*(1-fx) + grid[iy][(ix+1)%size]*fx
            b = grid[(iy+1)%size][ix]*(1-fx) + grid[(iy+1)%size][(ix+1)%size]*fx
            wet = a*(1-fy) + b*fy
            rough = max(.08, min(.98, source_pixels[4*(py*width+px)] * (1-wet_amount*wet)))
            result.extend((rough, rough, rough, 1.0))
    image = bpy.data.images.new(output_file, width=width, height=height)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(result)
    image.filepath_raw = str(OUT / output_file)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def scanned(name, color_file, rough_file, normal_file, strength, wet_file, seed, wet_amount):
    mat = solid(name, (.35, .3, .25))
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    color = bpy.data.images.load(str(TEXTURES / color_file), check_existing=True)
    color.pack()
    rough = wet_roughness(rough_file, wet_file, seed, wet_amount)
    for image, dest in ((color, "Base Color"), (rough, "Roughness")):
        node = nodes.new("ShaderNodeTexImage")
        node.image = image
        links.new(node.outputs["Color"], shader.inputs[dest])
    image = bpy.data.images.load(str(TEXTURES / normal_file), check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    image.pack()
    normal_image = nodes.new("ShaderNodeTexImage")
    normal_image.image = image
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = strength
    links.new(normal_image.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    return mat


wood = scanned("Wood | aged scanned grain",
               "fine_grained_wood_col_1k.jpg", "fine_grained_wood_rough_1k.jpg",
               "fine_grained_wood_nor_gl_1k.jpg", .48, "tavern_wood_wet_rough.png", 723, .52)
stone = scanned("Stone | grey scanned granite",
                "granite_tile_diff_1k.jpg", "granite_tile_rough_1k.jpg",
                "granite_tile_nor_gl_1k.jpg", .52, "tavern_stone_wet_rough.png", 947, .76)
wood_dark = solid("Timber | darkened edges", (.046, .024, .013), .84)
plaster = solid("Plaster | weathered wall", (.27, .245, .20), .94)
roof = solid("Roof | charcoal fired clay", (.047, .054, .055), .78)
iron = solid("Iron | aged hardware", (.07, .065, .052), .54, .72)
brass = solid("Brass | dulled fittings", (.21, .135, .063), .48, .7)
paper = solid("Window | old paper", (.40, .31, .20), .88)
lantern_red = solid("Lantern | vermilion paper", (.28, .018, .007), .78)
lantern_rib = solid("Lantern | dark ribs", (.09, .029, .012), .76)
grout = solid("Paving | dark joints", (.027, .031, .029), .95)
lantern_shader = lantern_red.node_tree.nodes.get("Principled BSDF")
lantern_shader.inputs["Emission Color"].default_value = (.32, .055, .006, 1)
lantern_shader.inputs["Emission Strength"].default_value = .22

# An original red paper map keeps fibre and staining visible without relying
# on Blender-only procedural nodes in the exported asset.
lantern_rng = random.Random(241)
lantern_pixels = array("f")
for py in range(512):
    for px in range(512):
        fibre = .012*math.sin(px*.38) + .009*math.sin(py*.19)
        stains = .035*max(0, math.sin(px*.025 + math.sin(py*.018)*1.3))
        red = max(.25, min(.56, .43 + fibre - stains + lantern_rng.uniform(-.012,.012)))
        lantern_pixels.extend((red, red*.22, red*.10, 1.0))
lantern_image = bpy.data.images.new("Tavern | paper lantern", width=512, height=512)
lantern_image.pixels.foreach_set(lantern_pixels)
lantern_image.filepath_raw = str(OUT / "tavern_lantern_color.png")
lantern_image.file_format = "PNG"
lantern_image.save()
lantern_image.pack()
lantern_texture = lantern_red.node_tree.nodes.new("ShaderNodeTexImage")
lantern_texture.image = lantern_image
lantern_red.node_tree.links.new(lantern_texture.outputs["Color"],
                                lantern_shader.inputs["Base Color"])

# Original, subtly mottled plaster colour map, packed for interchange export.
plaster_rng = random.Random(127)
grid = [[plaster_rng.random() for _ in range(18)] for _ in range(18)]
pixels = array("f")
for py in range(512):
    gy = py / 512 * 16
    iy, ty = int(gy), gy % 1
    for px in range(512):
        gx = px / 512 * 16
        ix, tx = int(gx), gx % 1
        low = grid[iy][ix]*(1-tx) + grid[iy][ix+1]*tx
        high = grid[iy+1][ix]*(1-tx) + grid[iy+1][ix+1]*tx
        stain = low*(1-ty) + high*ty
        value = max(.35, min(.72, .60 - .045*stain + plaster_rng.uniform(-.012,.012)))
        pixels.extend((value, value*.98, value*.93, 1.0))
plaster_image = bpy.data.images.new("Tavern | mottled plaster", width=512, height=512)
plaster_image.pixels.foreach_set(pixels)
plaster_image.filepath_raw = str(OUT / "tavern_plaster_color.png")
plaster_image.file_format = "PNG"
plaster_image.save()
plaster_image.pack()
plaster_texture = plaster.node_tree.nodes.new("ShaderNodeTexImage")
plaster_texture.image = plaster_image
plaster.node_tree.links.new(plaster_texture.outputs["Color"],
                           plaster.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])


def empty(name, parent=None, location=(0,0,0)):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = .10
    obj.parent = parent
    obj.location = location
    asset.objects.link(obj)
    return obj


root = empty("Tavern_Root")
root["units"] = "metres"
roots = {name: empty(name, root, location) for name, location in (
    ("Structure_Root", (0,0,0)),
    ("Door_Left_Root", (-.925,0,0)),
    ("Door_Right_Root", (.925,0,0)),
    ("Paving_Root", (0,0,0)),
    ("Lantern_Root", (-1.43,-.42,2.865)))}


class Parts:
    """One editable mesh per module, with independent loose geometry pieces."""

    def __init__(self, name, parent, materials):
        self.name, self.parent, self.materials = name, parent, materials
        self.vertices, self.faces, self.face_uvs, self.indices, self.smooth = [], [], [], [], []
        self.lookup = {}

    def face(self, coords, material, uvs=None, smooth=False):
        indices = []
        for point in coords:
            key = tuple(round(float(value), 7) for value in point)
            if key not in self.lookup:
                self.lookup[key] = len(self.vertices)
                self.vertices.append(point)
            indices.append(self.lookup[key])
        self.faces.append(tuple(indices))
        self.indices.append(material)
        self.smooth.append(smooth)
        if uvs is None:
            a, b, c = (Vector(p) for p in coords[:3])
            normal = (b - a).cross(c - a)
            axis = max(range(3), key=lambda i: abs(normal[i]))
            axes = ((1, 2), (0, 2), (0, 1))[axis]
            uvs = [(p[axes[0]] / .6, p[axes[1]] / .6) for p in coords]
        self.face_uvs.append(uvs)

    def box(self, center, size, material):
        x, y, z = center
        dx, dy, dz = (n / 2 for n in size)
        v = [(x-dx,y-dy,z-dz), (x+dx,y-dy,z-dz), (x+dx,y+dy,z-dz), (x-dx,y+dy,z-dz),
             (x-dx,y-dy,z+dz), (x+dx,y-dy,z+dz), (x+dx,y+dy,z+dz), (x-dx,y+dy,z+dz)]
        for indices in ((0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5),
                        (2,3,7,6), (3,0,4,7)):
            self.face([v[i] for i in indices], material)

    def bar_xz(self, a, b, y, width, depth, material):
        direction = Vector((b[0]-a[0], b[1]-a[1])).normalized()
        side = Vector((-direction.y, direction.x)) * width / 2
        corners = [(a[0]-side.x,a[1]-side.y), (b[0]-side.x,b[1]-side.y),
                   (b[0]+side.x,b[1]+side.y), (a[0]+side.x,a[1]+side.y)]
        front = [(x,y-depth/2,z) for x,z in corners]
        back = [(x,y+depth/2,z) for x,z in corners]
        self.face(front, material)
        self.face(list(reversed(back)), material)
        for i in range(4):
            j = (i+1) % 4
            self.face([front[i],back[i],back[j],front[j]], material)

    def torus_xz(self, center, radius, tube, material, major=16, minor=6):
        x, y, z = center
        for i in range(major):
            a0, a1 = 2*math.pi*i/major, 2*math.pi*(i+1)/major
            for j in range(minor):
                b0, b1 = 2*math.pi*j/minor, 2*math.pi*(j+1)/minor
                def point(a, b):
                    r = radius + tube*math.cos(b)
                    return (x+r*math.cos(a), y+tube*math.sin(b), z+r*math.sin(a))
                self.face([point(a0,b0),point(a0,b1),point(a1,b1),point(a1,b0)], material,
                          smooth=True)

    def diamond_xz(self, center, half_width, half_height, y, border, depth, material):
        x,z = center
        outer = [(x,z-half_height),(x+half_width,z),(x,z+half_height),(x-half_width,z)]
        inner = [(x,z-half_height+border),(x+half_width-border,z),
                 (x,z+half_height-border),(x-half_width+border,z)]
        def pt(p, yvalue):
            return (p[0], yvalue, p[1])
        front, back = y-depth/2, y+depth/2
        for i in range(4):
            j = (i+1)%4
            self.face([pt(outer[i],front),pt(outer[j],front),
                       pt(inner[j],front),pt(inner[i],front)], material)
            self.face([pt(inner[i],back),pt(inner[j],back),
                       pt(outer[j],back),pt(outer[i],back)], material)
            self.face([pt(outer[i],front),pt(outer[i],back),
                       pt(outer[j],back),pt(outer[j],front)], material)
            self.face([pt(inner[i],front),pt(inner[j],front),
                       pt(inner[j],back),pt(inner[i],back)], material)

    def cylinder_z(self, center, radius, height, material, segments=24):
        x,y,z = center
        for i in range(segments):
            a, b = 2*math.pi*i/segments, 2*math.pi*(i+1)/segments
            lo = [(x+radius*math.cos(t),y+radius*math.sin(t),z-height/2) for t in (a,b)]
            hi = [(p[0],p[1],z+height/2) for p in lo]
            self.face([lo[0],lo[1],hi[1],hi[0]], material, smooth=True)
        top = [(x+radius*math.cos(2*math.pi*i/segments),
                y+radius*math.sin(2*math.pi*i/segments),z+height/2) for i in range(segments)]
        bottom = [(p[0],p[1],z-height/2) for p in top]
        self.face(top, material)
        self.face(list(reversed(bottom)), material)

    def finish(self):
        mesh = bpy.data.meshes.new(self.name + "_mesh")
        pivot = self.parent.location
        local_vertices = [(p[0]-pivot.x,p[1]-pivot.y,p[2]-pivot.z) for p in self.vertices]
        mesh.from_pydata(local_vertices, [], self.faces)
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        asset.objects.link(obj)
        obj.parent = self.parent
        for mat in self.materials:
            mesh.materials.append(mat)
        uv = mesh.uv_layers.new(name="SurfaceUV")
        for poly, material, uvs, smooth in zip(mesh.polygons, self.indices, self.face_uvs, self.smooth):
            poly.material_index = material
            poly.use_smooth = smooth
            for index, coordinate in zip(poly.loop_indices, uvs):
                uv.data[index].uv = coordinate
        return obj


# Wall, posts, lintel and the projecting tiled eave are one removable module.
structure = Parts("Structure", roots["Structure_Root"], [wood, wood_dark, plaster, roof, stone, brass])
for side in (-1, 1):
    structure.box((side*1.56,.18,1.38), (.88,.24,2.72), 2)
    structure.box((side*1.04,-.04,1.42), (.18,.28,2.84), 0)
    structure.box((side*1.04,-.04,.12), (.28,.34,.24), 4)
    structure.box((side*1.94,-.015,1.40), (.14,.23,2.80), 0)
    # A shallow stone gate surround and short wooden support below the eave.
    structure.box((side*.965,-.20,1.32), (.08,.13,2.48), 4)
    structure.bar_xz((side*1.10,2.46),(side*1.34,2.66),-.20,.075,.12,0)
structure.box((0,-.206,2.53), (2.02,.13,.10), 4)
structure.box((0,-.04,2.68), (4.06,.32,.20), 0)
structure.box((0,-.12,2.84), (4.32,.46,.16), 1)
structure.box((0,-.30,2.77), (2.26,.22,.07), 1)
structure.box((0,-.32,2.83), (2.42,.27,.05), 1)
structure.box((0,.15,2.38), (1.96,.20,.12), 0)
structure.box((0,.07,2.52), (1.96,.16,.18), 0)
structure.box((0,-.02,.08), (1.96,.42,.16), 4)
structure.box((0,-.21,2.62), (.86,.06,.25), 1)
structure.box((0,-.245,2.62), (.77,.025,.17), 0)

# Hand-built strokes for the common sign 酒; no font asset is embedded.
sign_strokes = [
    ((-.10,2.665),(-.085,2.651)), ((-.103,2.63),(-.087,2.617)),
    ((-.10,2.59),(-.087,2.608)), ((-.047,2.676),(.105,2.676)),
    ((-.038,2.655),(.094,2.655)), ((-.038,2.655),(-.038,2.574)),
    ((.094,2.655),(.094,2.574)), ((-.038,2.574),(.094,2.574)),
    ((-.009,2.672),(-.009,2.612)), ((.048,2.672),(.048,2.618)),
    ((-.035,2.608),(.091,2.608)), ((-.035,2.588),(.091,2.588)),
]
for a,b in sign_strokes:
    structure.bar_xz(a,b,-.265,.006,.006,5)

# Semi-cylindrical roof tiles form a single editable eave mesh.
for i in range(36):
    center = -2.10 + i*.12
    lift = .10 * (abs(center)/2.10)**4
    for j in range(8):
        a, b = math.pi*j/8, math.pi*(j+1)/8
        x0, x1 = center + .058*math.cos(a), center + .058*math.cos(b)
        z0, z1 = 2.96 + lift + .034*math.sin(a), 2.96 + lift + .034*math.sin(b)
        structure.face([(x0,-.58,z0),(x0,.30,z0+.21),
                        (x1,.30,z1+.21),(x1,-.58,z1)], 3)
    cap = [(center+.055*math.cos(math.pi*j/12),-.582,
            2.96+lift+.035*math.sin(math.pi*j/12)) for j in range(13)]
    structure.face(cap, 3)
structure.finish()


def make_door(side):
    name = "Door_Left" if side < 0 else "Door_Right"
    parent = roots[name + "_Root"]
    door = Parts(name, parent, [wood, wood_dark, paper, iron, brass])
    center = side*.47
    door.box((center,.035,1.25), (.91,.085,2.34), 0)
    # Inset paper-backed lattice and thick timber stiles.
    door.box((center,-.024,1.77), (.68,.018,.91), 2)
    for dx in (-.41,.41):
        door.box((center+dx,-.073,1.25), (.085,.09,2.34), 0)
    for z in (.14,1.20,2.32):
        door.box((center,-.079,z), (.91,.09,.095), 0)
    for x in (center-.25,center,center+.25):
        door.box((x,-.072,1.77), (.027,.065,.90), 1)
    for z in (1.39,1.65,1.91,2.15):
        door.box((center,-.073,z), (.70,.065,.027), 1)
    # Four simple diamonds within each upper window.
    for zc in (1.52,1.79,2.04):
        for xc in (center-.125,center+.125):
            door.diamond_xz((xc,zc),.10,.09,-.115,.017,.022,0)
    for dx in (-.27,0,.27):
        door.box((center+dx,-.073,.66), (.014,.045,.92), 1)
    # Uneven small scratches on the lower wood panel, rather than a mirrored
    # ornamental pattern. They remain clear of the raised stiles and rails.
    scratches = random.Random(440 + side)
    for _ in range(18):
        x = center + scratches.uniform(-.32,.32)
        z = scratches.uniform(.28,.92)
        length = scratches.uniform(.045,.16)
        width = scratches.uniform(.001,.003)
        lean = scratches.uniform(-.006,.006)
        door.face([(x,-.0085,z),(x+width,-.0085,z),
                   (x+width+lean,-.0085,z+length),(x+lean,-.0085,z+length)],1)
    for x in (center-.34,center-.17,center,center+.17,center+.34):
        for z in (.23,1.12,2.25):
            door.box((x,-.127,z), (.025,.025,.025), 4)
    # Pair of iron ring pulls on the inner edges.
    handle_x = center - side*.30
    door.box((handle_x,-.115,1.02), (.075,.03,.09), 3)
    door.torus_xz((handle_x,-.148,.985), .045, .007, 4)
    return door.finish()


make_door(-1)
make_door(1)

# Flagstones have irregular chamfered outlines and separated joints. Each slab
# remains a loose mesh component even though the module exports as one mesh.
paving = Parts("Paving", roots["Paving_Root"], [stone, grout])
paving.box((0,-1.29,-.074), (4.25,3.02,.10), 1)
for row in range(6):
    for col in range(7):
        x = -1.82 + col*.61 + (.055 if row % 2 else 0) + random.uniform(-.010,.010)
        y = -.10 - row*.49 + random.uniform(-.006,.006)
        half_x = .292 - random.uniform(0,.025)
        half_y = .229 - random.uniform(0,.018)
        c0,c1,c2,c3 = (random.uniform(.020,.075) for _ in range(4))
        top = .025 + random.uniform(-.003,.003)
        outline = [(-half_x+c0,-half_y),(half_x-c1,-half_y),
                   (half_x,-half_y+c1),(half_x,half_y-c2),
                   (half_x-c2,half_y),(-half_x+c3,half_y),
                   (-half_x,half_y-c3),(-half_x,-half_y+c0)]
        lower = [(x+px,y+py,-.025) for px,py in outline]
        upper = [(x+px,y+py,top) for px,py in outline]
        paving.face(list(reversed(lower)), 0)
        cellx, celly = random.randrange(5), random.randrange(5)
        uv = [(cellx*.2+.015+(px+half_x)/(2*half_x)*.17,
               celly*.2+.015+(py+half_y)/(2*half_y)*.17) for px,py in outline]
        paving.face(upper, 0, uv)
        for i in range(8):
            j=(i+1)%8
            paving.face([lower[i],lower[j],upper[j],upper[i]], 0,
                        [(uv[i][0],uv[i][1]-.025),(uv[j][0],uv[j][1]-.025),
                         uv[j],uv[i]])
paving.finish()

# A ribbed paper lantern with visible cap, suspension and tassel.
lamp = Parts("Lantern", roots["Lantern_Root"], [lantern_red, lantern_rib, brass, wood_dark])
lx, ly = -1.43, -.42
lamp.cylinder_z((lx,ly,2.71), .009, .31, 3, 12)
profiles = [(2.28,.070),(2.31,.125),(2.36,.167),(2.46,.188),
            (2.56,.170),(2.61,.125),(2.64,.075)]
segments = 32
for n in range(len(profiles)-1):
    z0,r0 = profiles[n]
    z1,r1 = profiles[n+1]
    for j in range(segments):
        a, b = 2*math.pi*j/segments,2*math.pi*(j+1)/segments
        lamp.face([(lx+r0*math.cos(a),ly+r0*math.sin(a),z0),
                   (lx+r0*math.cos(b),ly+r0*math.sin(b),z0),
                   (lx+r1*math.cos(b),ly+r1*math.sin(b),z1),
                   (lx+r1*math.cos(a),ly+r1*math.sin(a),z1)], 0,
                  [(j/segments,(z0-2.28)/.36),((j+1)/segments,(z0-2.28)/.36),
                   ((j+1)/segments,(z1-2.28)/.36),(j/segments,(z1-2.28)/.36)], smooth=True)
for j in range(16):
    a=2*math.pi*j/16
    for n in range(len(profiles)-1):
        z0,r0=profiles[n]
        z1,r1=profiles[n+1]
        da=.012
        lamp.face([(lx+(r0+.001)*math.cos(a-da),ly+(r0+.001)*math.sin(a-da),z0),
                   (lx+(r0+.001)*math.cos(a+da),ly+(r0+.001)*math.sin(a+da),z0),
                   (lx+(r1+.001)*math.cos(a+da),ly+(r1+.001)*math.sin(a+da),z1),
                   (lx+(r1+.001)*math.cos(a-da),ly+(r1+.001)*math.sin(a-da),z1)], 1)
for z in (2.275,2.645):
    lamp.cylinder_z((lx,ly,z), .09, .035, 3)
    lamp.cylinder_z((lx,ly,z-.022), .055, .015, 2)
lamp.cylinder_z((lx,ly,2.19), .008, .16, 2, 12)
for i in range(9):
    a=2*math.pi*i/9
    length = .10 + .025*random.random()
    lamp.cylinder_z((lx+.018*math.cos(a),ly+.018*math.sin(a),2.16-length/2), .003, length, 2, 6)
lamp.finish()


def area(name, position, target, energy, size, color):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=energy
    data.shape="DISK"
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


def camera(name, position, target, lens):
    data=bpy.data.cameras.new(name)
    data.lens=lens
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
    return obj


world=bpy.data.worlds.new("Night | review only")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.12,.16,.22,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.18
scene.world=world
area("Moon fill", (1.8,-3.8,5.2), (0,0,1.2), 330, 4.5, (.62,.75,1.0))
area("Lantern warmth", (-1.6,-1.1,2.45), (-.7,0,1.7), 30, .75, (1.0,.38,.12))
area("Door bounce", (1.2,-2.2,2.1), (0,0,1.2), 55, 2.4, (1.0,.69,.45))
full=camera("Review | entrance", (3.35,-6.9,2.65), (0,-.32,1.48), 42)
detail=camera("Review | lantern and wood", (-2.8,-3.8,2.55), (-.85,-.05,1.77), 55)
paving_detail=camera("Review | wet paving", (-.7,-3.4,1.05), (0,-1.2,.02), 48)
scene.camera=full
scene.render.engine="CYCLES"
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1500
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "tavern_slice.blend"))
bpy.ops.object.select_all(action="DESELECT")
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT / "tavern_slice.glb"), export_format="GLB",
                          use_selection=True, export_extras=True,
                          export_yup=True, export_animations=False)
scene.render.filepath=str(OUT / "tavern_review_full.png")
bpy.ops.render.render(write_still=True)
scene.camera=detail
scene.render.resolution_x=1200
scene.render.resolution_y=1000
scene.render.filepath=str(OUT / "tavern_review_detail.png")
bpy.ops.render.render(write_still=True)
scene.camera=paving_detail
scene.render.resolution_x=1200
scene.render.resolution_y=900
scene.render.filepath=str(OUT / "tavern_review_paving.png")
bpy.ops.render.render(write_still=True)
