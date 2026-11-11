"""Place the nine unmodified diagnostic frames into one labelled timeline."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 30)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 24)
board = Image.new('RGB', (2400, 1990), '#181e24')
draw = ImageDraw.Draw(board)
draw.text((24, 16), 'STEEL CONTACT / 1.5m / same camera + light / old - ordinary - parry', font=font, fill='#f2e5cd')
draw.text((24, 60), 'OFFLINE actual GLBs. Example T=Stage+X / B=+Y / N=+Z. 80deg FOV. Not an SDK capture.', font=small, fill='#b9c5d0')
for row, ms in enumerate((33, 67, 167)):
    top = 110 + row * 625
    for column, (kind, label) in enumerate((('old', 'OLD: whole debris layer'), ('normal', 'ORDINARY: independent particles'), ('parry', 'PARRY: 90ms core + faster sparks'))):
        x = column * 800
        draw.text((x + 16, top), f'{ms}ms | {label}', font=small, fill='#e0c397' if kind != 'old' else '#c0cad3')
        board.paste(Image.open(HERE / f'metal_{ms:03d}ms_{kind}.png').convert('RGB'), (x, top + 30))
board.save(HERE / 'metal_1_5m_timeline.png')
