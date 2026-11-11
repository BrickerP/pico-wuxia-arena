"""Compose the unmodified same-camera rendered diagnostic frames with labels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent / 'review'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
font = ImageFont.truetype(FONT, 28)
small = ImageFont.truetype(FONT, 22)
for age in (33, 100, 233):
    board = Image.new('RGB', (1600, 2010), '#181e24')
    draw = ImageDraw.Draw(board)
    draw.text((24, 15), f'DRY SOFT CONTACT | {age}ms | before / independent-particle candidate', font=font, fill='#f1e7d4')
    draw.text((24, 55), 'OFFLINE actual GLBs + current actor. 80deg FOV. Example tangent; PICO trigger/readability unverified.', font=small, fill='#b5c1cc')
    for row, distance in enumerate((.8, 1.5, 3)):
        top = 105 + row * 630
        draw.text((20, top), f'{distance:.1f}m  BEFORE: current 3 layers', font=small, fill='#ccd1d7')
        draw.text((820, top), f'{distance:.1f}m  AFTER: core + 12 dry particles', font=small, fill='#ead1a0')
        for column, mode in enumerate(('before', 'after')):
            frame = Image.open(REVIEW / f'soft_{distance:.1f}m_{age:03d}ms_{mode}.png').convert('RGB')
            board.paste(frame, (column * 800, top + 30))
    board.save(REVIEW / f'soft_normal_distance_{age:03d}ms.png')
