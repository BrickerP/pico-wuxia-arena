"""Bake original portable PBR maps; source scans remain read-only."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'textures'
SOURCE = ROOT / 'ArtSource/tavern/textures'
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261111)
size = 512
y, x = np.mgrid[0:1:complex(size), 0:1:complex(size)]

def save(name, values):
    data = np.uint8(np.clip(values, 0, 1) * 255)
    Image.fromarray(data).save(OUT / (name + '.png'))

def normal(height, strength):
    dy, dx = np.gradient(height)
    v = np.dstack((-dx * strength, -dy * strength, np.ones_like(dx)))
    v /= np.linalg.norm(v, axis=2, keepdims=True)
    return v * .5 + .5

def low_noise(scale, seed):
    local = np.random.default_rng(seed)
    grid = Image.fromarray(np.uint8(local.random((scale, scale)) * 255))
    return np.asarray(grid.resize((size, size), Image.Resampling.BICUBIC), dtype=float) / 255

for channel, filename in [('color','granite_tile_diff_1k.jpg'),
                          ('normal','granite_tile_nor_gl_1k.jpg'),
                          ('rough','granite_tile_rough_1k.jpg')]:
    # First photographed tile interior, with the scan's grout excluded in all channels.
    img = Image.open(SOURCE / filename).crop((24,24,190,190)).resize((512,512), Image.Resampling.LANCZOS)
    arr = np.asarray(img.convert('RGB'), dtype=float) / 255
    if channel == 'color':
        arr *= np.array([.87, .94, 1.02])
    if channel == 'rough':
        arr = np.clip(arr * .66 + .17, .27, .8)
    save('stone_' + channel, arr)
    wet = arr.copy()
    if channel == 'color': wet *= .67
    if channel == 'rough': wet = wet * .44 + .08
    save('stone_wet_' + channel, wet)

for channel, filename in [('color','fine_grained_wood_col_1k.jpg'),
                          ('normal','fine_grained_wood_nor_gl_1k.jpg'),
                          ('rough','fine_grained_wood_rough_1k.jpg')]:
    arr = np.asarray(Image.open(SOURCE / filename).convert('RGB').resize((512,512)), dtype=float) / 255
    if channel == 'color':
        arr *= np.array([.80, .65, .52])
    if channel == 'rough':
        arr = arr * .55 + .23
    save('wood_' + channel, arr)

n = low_noise(22, 28)
fine = rng.random((size,size)) * .035
h = .55*n + .1*np.sin(x*180) + fine
save('roof_color', np.dstack((.23+.09*n+fine, .265+.10*n+fine, .27+.11*n+fine)))
save('roof_rough', .52+.22*n)
save('roof_normal', normal(h, 9))

n = low_noise(15, 71)
fine = rng.random((size,size)) * .035
# Low-wall damp line and long rain runoffs have an explicit vertical position.
damp = np.exp(-(1-y)*20) * (.4+.6*low_noise(10,33))
drip = np.maximum(0, np.sin(x*105+np.sin(x*33)*3))**14 * (.2+.8*y)
value = .71 + .12*n - damp*.27 - drip*.045 + fine
save('plaster_color', np.dstack((value*.94, value*.93, value*.84)))
save('plaster_rough', .88-damp*.22)
save('plaster_normal', normal(n*.22+fine, 5))

n = low_noise(34,17)
save('moss_color', np.dstack((.11+.08*n, .15+.10*n, .08+.05*n)))
save('moss_rough', .74+.14*n)
save('moss_normal', normal(n, 5))

manifest = {'status':'complete','source_scans':'Poly Haven CC0, see ArtSource/tavern/README.md',
            'procedural_original':['roof','plaster','moss'],
            'authored_uv':{'stone_repeat_m':.65,
                           'wood_longitudinal_repeat_m':1.25,'wood_transverse_repeat_m':.35,
                           'roof_pan':'one U repeat per .21m clay pan; V follows the overlapping row',
                           'plaster_repeat_m':[2.5,5.5],'moss_repeat_m':.65},
            'maps':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.png'))}}
(HERE/'texture_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Baked',len(manifest['maps']),'portable maps')
