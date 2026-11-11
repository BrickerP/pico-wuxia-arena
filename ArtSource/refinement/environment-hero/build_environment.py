"""06 private courtyard producer. No production resources are written.

Blender 4.5 LTS, one process; outputs stay below environment-hero.
Coordinates below: Blender metres, X across, +Y forward, Z height.
GLB export gives SDK metres X,+Y up,-Z forward, root at world origin.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import traceback

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = 20261111
rng = random.Random(SEED)
MODULES = {}
ANCHORS = {}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def material(name, color, roughness=.65, metallic=0, texture=None, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    node = m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color,1)
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Metallic'].default_value = metallic
    if texture:
        for suffix, target in [('color','Base Color'),('rough','Roughness'),('normal','Normal')]:
            image = bpy.data.images.load(str(HERE/'textures'/f'{texture}_{suffix}.png'),check_existing=True)
            if suffix != 'color': image.colorspace_settings.name = 'Non-Color'
            image.pack()
            t = m.node_tree.nodes.new('ShaderNodeTexImage')
            t.image = image
            if suffix == 'normal':
                n = m.node_tree.nodes.new('ShaderNodeNormalMap')
                n.inputs['Strength'].default_value = .55
                m.node_tree.links.new(t.outputs['Color'],n.inputs['Color'])
                m.node_tree.links.new(n.outputs['Normal'],node.inputs[target])
            else:
                m.node_tree.links.new(t.outputs['Color'],node.inputs[target])
    if emission:
        node.inputs['Emission Color'].default_value = (*emission,1)
        node.inputs['Emission Strength'].default_value = .45
    return m

class Mesh:
    def __init__(self,name,materials,bevel=0):
        self.name,self.materials,self.bevel=name,materials,bevel
        self.v,self.f,self.mi,self.uv,self.smooth=[],[],[],[],[]
        self.lookup={}
    def face(self,points,mat=0,uv=None,smooth=False):
        indices=[]
        for point in points:
            key=tuple(round(float(v),7) for v in point)
            if key not in self.lookup:
                self.lookup[key]=len(self.v);self.v.append(point)
            indices.append(self.lookup[key])
        self.f.append(tuple(indices))
        self.mi.append(mat)
        self.smooth.append(smooth)
        if uv is None:
            n=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0]))
            axis=max(range(3),key=lambda i:abs(n[i]))
            axes=((1,2),(0,2),(0,1))[axis]
            if self.materials[mat].name.startswith('EH Wall') and axis != 2:
                uv=[(p[axes[0]]/2.5,p[2]/5.5) for p in points]
            else:
                uv=[(p[axes[0]]/.65,p[axes[1]]/.65) for p in points]
        self.uv.append(uv)
    def box(self,c,size,mat=0):
        x,y,z=c; a,b,d=[t/2 for t in size]
        p=[(x-a,y-b,z-d),(x+a,y-b,z-d),(x+a,y+b,z-d),(x-a,y+b,z-d),
           (x-a,y-b,z+d),(x+a,y-b,z+d),(x+a,y+b,z+d),(x-a,y+b,z+d)]
        for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            points=[p[i] for i in q]
            uv=None
            if self.materials[mat].name.startswith('EH Timber'):
                long=max(range(3),key=lambda k:size[k])
                n=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0]))
                normal=max(range(3),key=lambda k:abs(n[k]))
                if long==normal:
                    axes=[k for k in range(3) if k!=long]
                    uv=[((t[axes[0]]-c[axes[0]])/.25,(t[axes[1]]-c[axes[1]])/.25) for t in points]
                else:
                    cross=next(k for k in range(3) if k not in (long,normal))
                    uv=[((t[cross]-c[cross])/.35,(t[long]-c[long])/1.25) for t in points]
            self.face(points,mat,uv)
    def beam(self,a,b,width,depth=None,mat=0):
        a,b=Vector(a),Vector(b)
        axis=(b-a).normalized()
        v=axis.cross(Vector((0,0,1)))
        if v.length<.01: v=axis.cross(Vector((1,0,0)))
        v.normalize(); v*=width/2
        w=axis.cross(v).normalized()*((depth or width)/2)
        p=[tuple(t+v*s+w*r) for t in (a,b) for s,r in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        for index,q in enumerate([(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]):
            points=[p[i] for i in q]
            uv=None
            if self.materials[mat].name.startswith('EH Timber'):
                if index<2:
                    uv=[((Vector(t)-a).dot(v.normalized())/.25,(Vector(t)-a).dot(w.normalized())/.25) for t in points]
                else:
                    tangent=(v if index in (2,4) else w).normalized()
                    uv=[((Vector(t)-a).dot(tangent)/.35,(Vector(t)-a).dot(axis)/1.25) for t in points]
            self.face(points,mat,uv)
    def cylinder(self,c,r,height,mat=0,segments=12):
        x,y,z=c
        rings=[[(x+r*math.cos(i*2*math.pi/segments),y+r*math.sin(i*2*math.pi/segments),z+h)
                for i in range(segments)] for h in (-height/2,height/2)]
        self.face(list(reversed(rings[0])),mat)
        self.face(rings[1],mat)
        for i in range(segments):
            j=(i+1)%segments
            self.face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]],mat,
                [(i/segments*2*math.pi*r/.35,0),((i+1)/segments*2*math.pi*r/.35,0),
                 ((i+1)/segments*2*math.pi*r/.35,height/1.25),(i/segments*2*math.pi*r/.35,height/1.25)],smooth=True)
    def finish(self):
        mesh=bpy.data.meshes.new(self.name+'_Mesh')
        mesh.from_pydata(self.v,[],self.f); mesh.update()
        obj=bpy.data.objects.new(self.name,mesh)
        bpy.context.scene.collection.objects.link(obj); obj.parent=ASSET
        for m in self.materials: mesh.materials.append(m)
        uv=mesh.uv_layers.new(name='SurfaceUV')
        for p,mi,coords,smooth in zip(mesh.polygons,self.mi,self.uv,self.smooth):
            p.material_index=mi; p.use_smooth=smooth
            for i,c in zip(p.loop_indices,coords): uv.data[i].uv=c
        if self.bevel:
            bpy.context.view_layer.objects.active=obj
            mod=obj.modifiers.new('Physical worn edge','BEVEL')
            mod.width=self.bevel; mod.segments=1
            bpy.ops.object.modifier_apply(modifier=mod.name)
        MODULES[self.name]=obj
        return obj

def anchor(name,p,role):
    obj=bpy.data.objects.new(name,None)
    bpy.context.scene.collection.objects.link(obj); obj.parent=ASSET; obj.location=p
    obj['role']=role
    ANCHORS[name]={'stage_m':[p[0],p[2],-p[1]],'role':role}
    return obj

def stone_ground():
    # Top of every combat flagstone is exactly Y=0 in SDK space.
    ground=Mesh('EH_GroundReceiver',[STONE,STONE_WET],.006)
    bed=Mesh('EH_MortarAndDrain',[MORTAR,STONE_WET,MOSS])
    bed.box((0,1.8,-.065),(10.8,9,.11))
    for row in range(18):
        y0=-2.7+row*.50
        for col in range(18):
            x0=-5.4+col*.60+(row%2)*.30
            x1=min(5.4,x0+.60)
            if x0>=5.4: continue
            # Ten millimetre shallow bed joints; no metre-scale black pits.
            wet=abs(x0)>2.3 or y0<-.6
            ground.box(((x0+x1)/2,y0+.25,-.045),(x1-x0-.010,.490,.090),int(wet))
    for x in (-3.35,3.35):
        bed.box((x,1.5,-.025),(.16,8.0,.03),1)
        for i in range(33):
            bed.box((x,-2.45+i*.24,-.004),(.18,.055,.025),1)
        for i in range(11):
            bed.box((x+(.12 if x<0 else -.12),-.8+i*.57,.001),(.035,.27,.004),2)
    ground.finish(); bed.finish()
    anchor('EH_ReceiverOrigin',(0,0,0),'ground receiver reference, SDK Y=0')

def window(mesh,x,y,z,w=1.2,h=1.4,side=False):
    # Inset warm paper, deep frames, fine lattice; frame faces toward courtyard.
    def c(u,v,d): return ((x+d,y+u,z+v) if side else (x+u,y+d,z+v))
    def sz(u,v,d): return ((d,u,v) if side else (u,d,v))
    mesh.box(c(0,0,0),sz(w,h,.035),2)
    for u in (-w/2,w/2): mesh.box(c(u,0,-.04),sz(.09,h+.12,.12),0)
    for v in (-h/2,h/2): mesh.box(c(0,v,-.045),sz(w+.12,.09,.13),0)
    for i in range(1,7): mesh.box(c(-w/2+w*i/7,0,-.075),sz(.026,h,.045),1)
    for v in (-h*.27,0,h*.27): mesh.box(c(0,v,-.075),sz(w,.033,.045),1)

def back_tavern():
    timber=Mesh('EH_TavernTimber',[WOOD,DARK],.009)
    walls=Mesh('EH_TavernWalls',[PLASTER,STONE_WET],.004)
    doors=Mesh('EH_EntryDoorsWindows',[WOOD,DARK,PAPER,BRASS],.004)
    # Building is a volume; side walls and a real roof close the old backdrop.
    for side in (-1,1):
        walls.box((side*3.65,5.65,1.45),(4.35,.28,2.9))
        walls.box((side*5.72,7.0,2.45),(.24,2.7,4.9))
        walls.box((side*3.65,5.42,.18),(4.35,.29,.36),1)
    walls.box((0,5.65,3.9),(11.65,.28,2.0))
    walls.box((0,8.32,2.4),(11.65,.22,4.8))
    for x in [-5.65,-3.6,-1.4,1.4,3.6,5.65]:
        timber.box((x,5.24,2.45),(.23,.29,4.9))
        walls.box((x,5.22,.16),(.4,.43,.32),1)
        timber.box((x,5.18,2.94),(.34,.45,.16),1)
        # Corbel brackets carry the eave; grain direction follows beam geometry.
        for k in range(3):
            timber.box((x,5.10-k*.10,2.98+k*.09),(.32+k*.04,.48+k*.10,.10))
        timber.beam((x,4.82,2.48),(x,5.22,2.9),.12)
    for z in [.43,2.85,3.15,4.8]: timber.box((0,5.23,z),(11.7,.25,.17))
    timber.box((0,4.85,3.13),(12.1,.23,.22))
    # Door is large enough for a believable person and behind the combat lane.
    for side in (-1,1):
        x=side*.64
        doors.box((x,5.39,1.42),(1.24,.14,2.65))
        window(doors,x,5.28,1.95,1.03,1.15)
        for k in range(5): doors.box((x-.48+k*.24,5.29,.65),(.018,.035,.91),1)
        doors.cylinder((side*.19,5.23,1.03),.065,.03,3)
    for x in [-4.62,-2.47,2.47,4.62]: window(doors,x,5.42,1.7,1.34,1.5)
    for x in [-4.55,-2.3,0,2.3,4.55]: window(doors,x,5.44,3.97,1.45,1.12)
    # Threshold worn tread and continuous covered gallery.
    for y,h in [(4.94,.07),(5.20,.14)]: walls.box((0,y,h/2),(2.78,.32,h),1)
    walls.box((0,5.12,.06),(11.8,.88,.12),1)
    # A legible 酒 plaque provides the one distinctive entrance landmark.
    timber.box((0,4.62,2.95),(1.64,.16,.40),1)
    timber.box((0,4.52,2.95),(1.50,.05,.30))
    strokes=[((-.10,.065),(-.085,.051)),((-.103,.03),(-.087,.017)),
       ((-.10,-.01),(-.087,.008)),((-.047,.076),(.105,.076)),
       ((-.038,.055),(.094,.055)),((-.038,.055),(-.038,-.026)),
       ((.094,.055),(.094,-.026)),((-.038,-.026),(.094,-.026)),
       ((-.009,.072),(-.009,.012)),((.048,.072),(.048,.018)),
       ((-.035,.008),(.091,.008)),((-.035,-.012),(.091,-.012))]
    for a,b in strokes:
        doors.beam((a[0]*2.0,4.478,2.90+a[1]*2.0),
                   (b[0]*2.0,4.478,2.90+b[1]*2.0),.019,.014,3)
    timber.finish(); walls.finish(); doors.finish()

def roof(name,cx,cy,width,depth,base,rise,angle=0):
    mesh=Mesh(name,[ROOF,ROOF_EDGE])
    ca,sa=math.cos(angle),math.sin(angle)
    def pt(x,y,z): return (cx+ca*x-sa*y,cy+sa*x+ca*y,z)
    pitch=.21
    cols=math.ceil(width/pitch)
    def height(x,y):
        t=abs(y)/(depth/2)
        return base+rise*(1-t)**1.6+.22*(abs(x)/(width/2))**8+.16*t**7
    # Separate overlapping clay pans, rolled cap rows and a curved eave silhouette.
    for row in range(7):
        for side in (-1,1):
            y0=side*(row/7*(depth/2))
            y1=side*min(depth/2,(row+1.16)/7*(depth/2))
            for col in range(cols):
                x=-width/2+col*pitch
                x1=min(width/2,x+pitch-.012)
                zoff=rng.uniform(-.006,.006)
                p=[pt(xx,yy,height(xx,yy)+zoff) for xx,yy in [(x,y0),(x1,y0),(x1,y1),(x,y1)]]
                if side<0: p.reverse()
                mesh.face(p,0,[(0,0),(1,0),(1,.7),(0,.7)])
                # Raised barrel cap has real silhouette and visible thickness.
                for j in range(5):
                    a,b=math.pi*j/5,math.pi*(j+1)/5
                    xx0=x+.042*math.cos(a); xx1=x+.042*math.cos(b)
                    points=[pt(xx0,y0,height(x,y0)+.035*math.sin(a)+.012),
                            pt(xx0,y1,height(x,y1)+.035*math.sin(a)+.012),
                            pt(xx1,y1,height(x,y1)+.035*math.sin(b)+.012),
                            pt(xx1,y0,height(x,y0)+.035*math.sin(b)+.012)]
                    if side<0: points.reverse()
                    mesh.face(points,1,smooth=True)
    # Ridge and gable end boards are closed volumes, with restrained upturned ends.
    for i in range(cols):
        x=-width/2+(i+.5)*pitch
        p0=pt(x-pitch/2,0,height(x,0)+.10)
        p1=pt(x+pitch/2,0,height(x,0)+.10)
        mesh.beam(p0,p1,.14,.16,1)
    for side in (-1,1):
        for i in range(16):
            x0=-width/2+i*width/16; x1=x0+width/16
            mesh.beam(pt(x0,side*depth/2,height(x0,side*depth/2)-.02),
                      pt(x1,side*depth/2,height(x1,side*depth/2)-.02),.085,.12,1)
    if not name.startswith('EH_Town'):
        rafters=Mesh(name+'_Rafters',[WOOD],.005)
        for col in range(math.ceil(width/.46)+1):
            x=min(width/2,-width/2+col*.46)
            for side in (-1,1):
                for j in range(4):
                    y0=side*depth/2*j/4;y1=side*depth/2*(j+1)/4
                    rafters.beam(pt(x,y0,height(x,y0)-.09),pt(x,y1,height(x,y1)-.09),.06,.095)
        rafters.finish()
    return mesh.finish()

def side_galleries():
    wood=Mesh('EH_SideGalleryTimber',[WOOD,DARK],.008)
    wall=Mesh('EH_SideGalleryWalls',[PLASTER,STONE_WET],.004)
    windows=Mesh('EH_SideGalleryWindows',[WOOD,DARK,PAPER],.003)
    for side in (-1,1):
        x=side*5.0
        wall.box((side*5.75,1.35,1.36),(.24,7.7,2.72))
        wall.box((side*5.58,1.35,.18),(.34,7.7,.36),1)
        wall.box((side*4.85,1.35,.08),(1.7,7.9,.16),1)
        for y in [-2.35,-.45,1.45,3.35,5.25]:
            wood.cylinder((side*4.12,y,1.43),.105,2.7)
            wall.box((side*4.12,y,.18),(.36,.36,.36),1)
            wood.box((side*4.12,y,2.65),(.38,.40,.12))
            wood.beam((side*4.12,y,2.25),(side*4.55,y,2.70),.11)
            wood.beam((side*4.12,y,2.45),(side*4.12,y+.43,2.72),.10)
        wood.box((side*4.12,1.45,2.79),(.19,8.1,.22))
        for y in [-1.35,.55,2.45,4.35]: window(windows,side*5.6,y,1.65,1.25,1.25,True)
        roof('EH_WestRoof' if side<0 else 'EH_EastRoof',side*5.0,1.35,8.45,2.65,2.86,.63,math.pi/2)
    wood.finish(); wall.finish(); windows.finish()

def props_and_water():
    props=Mesh('EH_CourtyardLife',[WOOD,DARK,BRASS,CLAY,MOSS],.006)
    pond=Mesh('EH_StonePond',[STONE_WET],.018)
    water=Mesh('EH_PondAndPuddles',[WATER])
    # A long shallow pond fills one side view, outside the battle area.
    pond.box((3.15,3.35,.15),(.8,2.8,.3))
    water.box((3.15,3.35,.307),(.69,2.65,.004))
    for x in (2.70,3.60): pond.box((x,3.35,.26),(.13,3.0,.18))
    for y in (1.88,4.82): pond.box((3.15,y,.26),(1.0,.13,.18))
    # Two clear step stones create a small exploration memory point.
    for y in (2.7,3.4,4.1):
        pond.box((3.15,y,.36),(1.12,.40,.09))
        for x in (2.85,3.45):pond.box((x,y,.19),(.16,.26,.30))
    # Water stays within the side low points. Central combat lane remains unobstructed.
    for side in (-1,1):
        for y in (-1.3,.9,4.35):
            x=side*(2.7+rng.uniform(0,.3))
            points=[(x+math.cos(i*math.pi/8)*(.42+rng.uniform(-.06,.04)),
                     y+math.sin(i*math.pi/8)*(.25+rng.uniform(-.04,.03)),.002) for i in range(16)]
            water.face(points,0)
    # Bench, drinks table, stacked wine jars and timber firewood stay under dry eaves.
    for x,y in [(-4.5,.65),(-4.5,3.15),(4.6,-1.3)]:
        props.box((x,y,.51),(.5,1.35,.085))
        for dy in (-.47,.47):
            for dx in (-.15,.15): props.box((x+dx,y+dy,.26),(.075,.075,.5))
    for i in range(8):
        props.beam((-5.2,-1.9+i*.11,.25),(-4.7,-1.9+i*.11,.25),.095,.095,0)
    # Restrained shrub at the wall base; no foliage alpha cards or center occlusion.
    for i in range(28):
        x=rng.uniform(-5.4,-4.8); y=rng.uniform(4.7,5.15)
        props.beam((x,y,.06),(x+.1,y+.05,rng.uniform(.25,.8)),.035,.035,4)
    props.finish(); pond.finish(); water.finish()

def reuse_crafted_props():
    # Only the four owned source modules, never old paving/railings/lamps.
    # Source filter keeps active scene ancestry, then all placement is rebaked here.
    sys.path.insert(0,str(ROOT/'ArtSource/refinement/environment'))
    import render_environment_review as previous
    sys.path.insert(0,str(ROOT/'ArtSource/tripo-warrior'))
    from prepare_rigged_warrior import read_glb,encode_glb
    source=ROOT/'ArtSource/tavern/courtyard_details.glb'
    doc,blob=read_glb(source)
    selected=['TeaTable_Root','Stool_Root','WineJars_Root','StoneLotusBasin_Root']
    subset,selection=previous.active_subset(doc,selected,[])
    path=HERE/'review'/'crafted_props_input.glb'
    path.write_bytes(encode_glb(subset,blob))
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported=list(bpy.context.selected_objects)
    targets={'TeaTable_Root':(-4.7,2.0,.16),'Stool_Root':(-3.65,1.65,0),
             'WineJars_Root':(-3.5,4.7,0),'StoneLotusBasin_Root':(-3.05,-1.15,0)}
    for name,target in targets.items():
        obj=next(o for o in imported if o.name==name)
        obj.location=target
    for obj in imported:
        if obj.type=='MESH':
            bpy.context.view_layer.update()
            frame=obj.matrix_world.copy()
            obj.parent=ASSET;obj.matrix_world=frame
            obj.name='EH_Reuse_'+obj.name
            MODULES[obj.name]=obj
    for obj in imported:
        if obj.type!='MESH':bpy.data.objects.remove(obj,do_unlink=True)
    (HERE/'review'/'props_provenance.json').write_text(json.dumps({
        'source':'ArtSource/tavern/courtyard_details.glb','sha256':sha(source),
        'selection':selection,'target_blender_m':targets},indent=2)+'\n')

def lanterns():
    metal=Mesh('EH_LanternFittings',[DARK,BRASS])
    paper=Mesh('EH_LanternPaper',[LANTERN])
    points=[(-2.15,4.78,2.7),(2.15,4.78,2.7),(-4.03,-.48,2.25),(4.03,1.4,2.25)]
    for index,(x,y,z) in enumerate(points):
        metal.cylinder((x,y,z+.48),.014,.55,0,8)
        rows=10; cols=24
        for j in range(rows):
            a0=-math.pi/2+math.pi*j/rows; a1=a0+math.pi/rows
            for i in range(cols):
                b0=i*2*math.pi/cols; b1=b0+2*math.pi/cols
                def pt(a,b):
                    radius=.24*max(.40,math.cos(a))*(1+.027*math.cos(b*12))
                    return (x+radius*math.cos(b),y+radius*math.sin(b),z+.32*math.sin(a))
                paper.face([pt(a0,b0),pt(a0,b1),pt(a1,b1),pt(a1,b0)],0,
                    [(i/cols,j/rows),((i+1)/cols,j/rows),((i+1)/cols,(j+1)/rows),(i/cols,(j+1)/rows)],smooth=True)
        # Thin bamboo ribs follow the paper shell, visibly distinct at normal distance.
        for rib in range(12):
            b=rib*2*math.pi/12
            for j in range(rows):
                a0=-math.pi/2+math.pi*j/rows;a1=a0+math.pi/rows
                def rp(a):
                    r=.24*max(.40,math.cos(a))*1.027+.002
                    return (x+r*math.cos(b),y+r*math.sin(b),z+.32*math.sin(a))
                metal.beam(rp(a0),rp(a1),.0065,.0065,0)
        for h in (-.315,.315): metal.cylinder((x,y,z+h),.105,.04,1,20)
        for k in range(5): metal.cylinder((x+(k-2)*.014,y,z-.49),.005,.28,1,6)
        anchor(f'EH_Light_Lantern_{index+1:02}',(x,y-.08,z),'warm point light; 07 sets intensity/range')
    metal.finish(); paper.finish()

def distant_context():
    walls=Mesh('EH_DistantTownWalls',[DISTANT,DARK,PAPER])
    # Adjacent three-storey town silhouette clears the near eave in the player view.
    for i,(x,y,w,d,h) in enumerate([(-8.9,10.5,3.1,3.6,9.9),(8.9,10.8,3.5,4,9.6)]):
        walls.box((x,y,h/2),(w,d,h))
        for dx in (-w/2,0,w/2):walls.box((x+dx,y-d/2-.02,h/2),(.10,.08,h),1)
        for z in (h-3,h-1.5,h-.1):walls.box((x,y-d/2-.03,z),(w,.10,.10),1)
        for dx in (-.65,.65):walls.box((x+dx,y-d/2-.05,h-.7),(.55,.04,.55),2)
        roof(f'EH_TownRoof_{i+1}',x,y,w+.6,d+.6,h,.9)
        roof(f'EH_TownLowerEave_{i+1}',x,y,w+.75,d+.75,h-2.5,.45)
    walls.finish()
    anchor('EH_Light_CourtMoon',(-4,2,7),'cool overhead key position for 07')
    anchor('EH_CombatClearCenter',(0,2.4,0),'clear combat reference; Y=0 floor')

def setup():
    global ASSET,STONE,STONE_WET,WOOD,DARK,PLASTER,ROOF,ROOF_EDGE,PAPER,BRASS,MORTAR,MOSS,WATER,CLAY,LANTERN,DISTANT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'
    ASSET=bpy.data.objects.new('EnvironmentHero_Root',None)
    scene.collection.objects.link(ASSET)
    ASSET['units']='metres'; ASSET['stage_placement']='identity, world origin (0,0,0)'
    ASSET['ground_datum']='SDK Y=0; remove old tavern, forecourt and courtyard_details'
    STONE=material('EH Stone | walked granite',(.40,.43,.45),texture='stone')
    STONE_WET=material('EH Stone | low damp granite',(.3,.34,.36),.28,texture='stone_wet')
    WOOD=material('EH Timber | aged grain',(.21,.11,.055),texture='wood')
    DARK=material('EH Timber | end grain recess',(.034,.024,.016),.78)
    PLASTER=material('EH Wall | rain stained lime',(.65,.62,.53),texture='plaster')
    ROOF=material('EH Roof | fired clay PBR',(.2,.24,.25),texture='roof')
    ROOF_EDGE=material('EH Roof | rolled tile caps',(.035,.043,.046),.57)
    PAPER=material('EH Windows | warm paper',(.38,.25,.115),.9,emission=(.28,.12,.028))
    BRASS=material('EH Fittings | aged bronze',(.26,.15,.048),.38,.68)
    MORTAR=material('EH Ground | damp shallow joints',(.13,.145,.14),.88)
    MOSS=material('EH Moss | damp wall base',(.14,.2,.09),texture='moss')
    WATER=material('EH Water | opaque shallow pool',(.035,.067,.06),.14,.12)
    CLAY=material('EH Jars | dark glazed earthenware',(.11,.049,.021),.21)
    LANTERN=material('EH Lantern | vermilion paper',(.48,.075,.017),.78,emission=(.6,.065,.01))
    lantern_image=bpy.data.images.load(str(ROOT/'ArtSource/tavern/tavern_lantern_color.png'),check_existing=True)
    lantern_image.pack()
    lantern_tex=LANTERN.node_tree.nodes.new('ShaderNodeTexImage');lantern_tex.image=lantern_image
    LANTERN.node_tree.links.new(lantern_tex.outputs['Color'],LANTERN.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    DISTANT=material('EH Town | distant slate plaster',(.035,.055,.06),.9)

def export():
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    ASSET.select_set(True)
    for o in ASSET.children: o.select_set(True)
    path=HERE/'courtyard_hero.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
        export_yup=True,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
    points=[o.matrix_world@Vector(p) for o in MODULES.values() for p in o.bound_box]
    bounds={'min':[min(p.x for p in points),min(p.z for p in points),-max(p.y for p in points)],
            'max':[max(p.x for p in points),max(p.z for p in points),-min(p.y for p in points)]}
    manifest={'status':'complete','candidate':path.name,'sha256':sha(path),
      'source_commit':'562449af40ee984ddd8ef61be5c339ac9bea2de5',
      'source_tavern_sha256':sha(ROOT/'ArtSource/tavern/tavern_slice.glb'),
      'producer_sha256':sha(Path(__file__)),'coordinates':'SDK metres, +Y up, -Z forward',
      'load_position_stage_m':[0,0,0],'load_rotation':'identity','load_scale':[1,1,1],
      'bounds_stage_m':bounds,'ground_top_stage_y_m':0,
      'replace_assets':['tavern_slice.glb','forecourt.glb','courtyard_details.glb'],
      'ground_receivers':['EH_GroundReceiver','EH_MortarAndDrain'],
      'modules':{n:{'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for n,o in MODULES.items()},
      'anchors':ANCHORS,'portable_maps':'texture_manifest.json',
      'limitations':['Not installed in PICO; Root owns build/device/integration',
                      'Offline lamps are review lights; 07 must recreate native lights from anchors',
                      'Opaque non-transmissive water avoids unsupported refraction; reflection needs native IBL',
                      'No collision/navmesh; existing fixed combat controls retained',
                      'Enemy old foot Y=.028 requires Root choose Y=0 or document .028 clearance']}
    (HERE/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

def studio():
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.world=bpy.data.worlds.new('Offline controlled cool overcast')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.065,.09,.12,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
    for name,p,energy,color,size in [('Moon soft key',(-2,1.5,7),1400,(.63,.78,1),7),
                                   ('Neutral eye fill',(1,-2,4),850,(.85,.90,1),5),
                                   ('Tavern spill',(0,4.8,3),500,(1,.54,.23),4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.size=size
        o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=p
        o.rotation_euler=(Vector((0,3,1))-o.location).to_track_quat('-Z','Y').to_euler()
    for i,p in enumerate([(-2.15,4.70,2.7),(2.15,4.70,2.7),(-4.03,-.56,2.25),(4.03,1.32,2.25)]):
        name=f'EH_Light_Lantern_{i+1:02}'
        data=bpy.data.lights.new('Offline '+name,'POINT');data.energy=32;data.color=(1,.32,.07);data.shadow_soft_size=.25
        o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=p
    data=bpy.data.cameras.new('Offline normal player eye');data.lens=18;data.clip_start=.03
    cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
    return scene,cam

VIEWS={'player':((0,0,1.6),(0,6,1.9)),
       'explore':((1.5,.4,1.6),(4.1,3.1,1.55)),
       'wall_3m':((2.6,1.8,1.6),(5.6,1.8,1.6)),
       'wall_1p5m':((4.1,1.8,1.6),(5.6,1.8,1.6)),
       'wall_0p8m':((4.8,1.8,1.6),(5.6,1.8,1.6))}

def render_review(phase):
    scene,cam=studio()
    for name,(p,target) in VIEWS.items():
        cam.location=p;cam.rotation_euler=(Vector(target)-Vector(p)).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(HERE/'review'/f'{phase}_{name}.png')
        bpy.ops.render.render(write_still=True)
    (HERE/'review'/f'{phase}_evidence.json').write_text(json.dumps({
        'kind':'offline GLB reimport review, not PICO runtime proof',
        'camera_blender_m':VIEWS,'lens_mm':18,'sensor_width_mm':36,
        'resolution':[1200,1200],'lighting':'same controlled overcast + fill + spill + four lamp points in both phases',
        'source_commit':'562449af40ee984ddd8ef61be5c339ac9bea2de5',
        'input_sha256':sha(HERE/'courtyard_hero.glb') if phase=='after' else {
            name:sha(ROOT/'ArtSource/tavern'/f'{name}.glb')
            for name in ('tavern_slice','forecourt','courtyard_details')}},indent=2)+'\n')

def before():
    # Reuse active-scene filtering from the existing review, never orphan nodes.
    sys.path.insert(0,str(ROOT/'ArtSource/refinement/environment'))
    import render_environment_review as previous
    inputs=[]
    for label,p in [('tavern_slice',(0,0,-4)),('forecourt',(0,0,-4)),('courtyard_details',(0,0,0))]:
        inputs.append(previous.import_asset(label,ROOT/'ArtSource/tavern'/f'{label}.glb',p,[],[],HERE/'review'/'baseline'))
    (HERE/'review'/'baseline'/'inputs_manifest.json').write_text(json.dumps(inputs,indent=2)+'\n')
    render_review('before')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['after','before'],default='after')
    parser.add_argument('--no-render',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    setup()
    if args.phase=='before':
        before();return
    stone_ground();back_tavern()
    roof('EH_TavernMainRoof',0,6.85,12.5,4.35,4.94,1.25)
    roof('EH_TavernPorchRoof',0,5.05,12.2,1.82,3.08,.28)
    side_galleries();props_and_water();reuse_crafted_props();lanterns();distant_context()
    export()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'courtyard_hero.blend'))
    if not args.no_render:
        # Review the deliverable GLB, including embedded exported maps, not just the .blend.
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(HERE/'courtyard_hero.glb'))
        render_review('after')
    print('ENVIRONMENT_HERO_COMPLETE',sha(HERE/'courtyard_hero.glb'))

if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
