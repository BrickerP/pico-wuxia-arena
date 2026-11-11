"""Assemble labels around unchanged offline render pixels, with SHA receipts."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
OUT=HERE/'review'
FONT='/System/Library/Fonts/Supplemental/Songti.ttc'
large=ImageFont.truetype(FONT,38)
small=ImageFont.truetype(FONT,25)
receipt={}
for view,label in [('player','站立主视角'),('explore','侧向探索视角')]:
    canvas=Image.new('RGB',(2400,1370),(23,27,31))
    draw=ImageDraw.Draw(canvas)
    for col,phase,title in [(0,'before','之前：单片门墙与大黑缝'),(1,'after','之后：双层酒馆、围廊与连续石路')]:
        p=OUT/f'{phase}_{view}.png'
        canvas.paste(Image.open(p).convert('RGB'),(col*1200,90))
        draw.text((col*1200+25,23),title,font=large,fill=(238,235,222))
        receipt[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    draw.text((24,1342),f'{label} · 同机位/同灯光 · 1.6m眼高 · 实际GLB重导入 · 离线资产对照，非PICO设备截图',font=small,fill=(205,211,216),anchor='ls')
    canvas.save(OUT/f'comparison_{view}.png')

canvas=Image.new('RGB',(2400,930),(23,27,31));draw=ImageDraw.Draw(canvas)
for i,(view,label) in enumerate([('wall_3m','3米'),('wall_1p5m','1.5米'),('wall_0p8m','0.8米')]):
    p=OUT/f'after_{view}.png'
    canvas.paste(Image.open(p).convert('RGB').resize((800,800),Image.Resampling.LANCZOS),(i*800,70))
    draw.text((i*800+24,18),f'侧廊 · {label}',font=large,fill=(238,235,222))
    receipt[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
draw.text((24,909),'1.6m站立眼高 · 18mm/36mm镜头 · 同一GLB与灯光 · 石基、木纹、雨痕和窗格的常规距离检查',font=small,fill=(205,211,216),anchor='ls')
canvas.save(OUT/'distance_review.png')
(OUT/'board_receipt.json').write_text(json.dumps({
    'candidate_sha256':hashlib.sha256((HERE/'courtyard_hero.glb').read_bytes()).hexdigest(),
    'render_pixels_edited':False,'input_images':receipt,
    'comparison_camera_equal':json.loads((OUT/'before_evidence.json').read_text())['camera_blender_m']==json.loads((OUT/'after_evidence.json').read_text())['camera_blender_m']},indent=2)+'\n')
print('Wrote two comparison boards and the distance review')
