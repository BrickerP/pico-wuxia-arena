from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent;OUT=HERE/'review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((HERE/'candidate_manifest.json').read_text());e=json.loads((OUT/'render_evidence.json').read_text())
assert m['sha256']==e['candidate_sha256']==sha(HERE/m['candidate'])
for n,h in e['images'].items():assert sha(OUT/n)==h,n
canvas=Image.new('RGB',(2400,1390),(24,27,30));d=ImageDraw.Draw(canvas)
font='/System/Library/Fonts/Supplemental/Songti.ttc';large=ImageFont.truetype(font,34);small=ImageFont.truetype(font,24)
for col,phase,title in [(0,'before','64da：九窗共享核心'),(1,'after','静态合批：保材质与属性布局')]:
    canvas.paste(Image.open(OUT/f'{phase}_static_environment.png').convert('RGB'),(col*1200,90))
    d.text((col*1200+24,24),title,font=large,fill=(238,233,222))
d.text((24,1320),'唯一一组既有机位 · 实际GLB同灯离线对照 · 仅静态环境；NPC/手刀不属于此GLB，非原生APK验收',font=small,fill=(208,215,220))
d.text((24,1356),f'候选 SHA256 {m["sha256"]}',font=small,fill=(154,166,176))
output=OUT/'comparison.png';canvas.save(output)
(OUT/'board_receipt.json').write_text(json.dumps({'candidate_sha256':m['sha256'],'source_sha256':m['source_sha256'],
 'source_images':e['images'],'pixels_repainted':False,'board_sha256':sha(output)},indent=2)+'\n')
print('STATIC_BATCH_COMPARISON_READY',m['sha256'])
