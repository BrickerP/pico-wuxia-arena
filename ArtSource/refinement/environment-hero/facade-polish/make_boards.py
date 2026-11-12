from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;OUT=HERE/'review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((HERE/'candidate_manifest.json').read_text());e=json.loads((OUT/'render_evidence.json').read_text())
assert m['sha256']==e['candidate_sha256']==sha(HERE/m['candidate'])
for name,digest in e['images'].items():assert sha(OUT/name)==digest,name
font='/System/Library/Fonts/Supplemental/Songti.ttc';large=ImageFont.truetype(font,34);small=ImageFont.truetype(font,24)
boards={}
for view,label in [('facade','正常站立眼高整立面'),('near_1p5m','1.5米局部')]:
    canvas=Image.new('RGB',(2400,1390),(24,27,30));draw=ImageDraw.Draw(canvas)
    for col,phase,title in [(0,'before','之前：原生已验证9b单窗庭院'),(1,'after','之后：成套共享窗与贴合瓦口')]:
        canvas.paste(Image.open(OUT/f'{phase}_{view}.png').convert('RGB'),(col*1200,90))
        draw.text((col*1200+24,24),title,font=large,fill=(239,233,222))
    draw.text((24,1320),f'{label} · 同机位同灯 / 当前clean-coat guard对应源 · 实际GLB离线图，非PICO端内图',font=small,fill=(208,215,220))
    draw.text((24,1356),f'候选SHA256 {m["sha256"]}',font=small,fill=(154,166,176))
    name=f'comparison_{view}.png';canvas.save(OUT/name);boards[name]=sha(OUT/name)
(OUT/'board_receipt.json').write_text(json.dumps({'candidate_sha256':m['sha256'],'source_sha256':m['source_sha256'],
 'pixels_repainted':False,'boards':boards,'actor_png_sha256':e['actor_png_sha256'],'formal_actor_ktx_sha256':e['formal_actor_ktx_sha256']},indent=2)+'\n')
print('FACADE_BOARDS_READY',m['sha256'])
