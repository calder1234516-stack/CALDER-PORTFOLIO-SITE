"""
process_stack.py
Copies Parsons stack images into meltdown/stack_web/ with short sequential filenames.
Converts all formats (webp, png, jpg) to JPEG at quality 85.
"""

import os
from PIL import Image

JPEG_QUALITY = 85

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STACK_SRC = r'C:\Users\Calder S. Anderson\Desktop\PARSONS SENIOR YEAR\STUDIO\stack'
DST_BASE  = os.path.join(BASE_DIR, 'stack_web')

CATS = [
    ('SUBSTRATE  MATERIAL WORLD', 'substrate'),
    ('MACHINE',                   'machine'),
    ('CIRCULATION',               'circulation'),
    ('REPRESENTATION',            'representation'),
    ('CONTROL',                   'control'),
]

EXTS = {'.jpg', '.jpeg', '.png', '.webp'}

for src_name, dst_name in CATS:
    src_dir = os.path.join(STACK_SRC, src_name)
    dst_dir = os.path.join(DST_BASE, dst_name)
    os.makedirs(dst_dir, exist_ok=True)

    files = sorted([
        f for f in os.listdir(src_dir)
        if os.path.splitext(f)[1].lower() in EXTS
    ])

    written = 0
    for i, fname in enumerate(files, 1):
        src_file = os.path.join(src_dir, fname)
        dst_file = os.path.join(dst_dir, f'{i:03d}.jpg')
        try:
            with Image.open(src_file) as img:
                img = img.convert('RGB')
                img.save(dst_file, 'JPEG', quality=JPEG_QUALITY, optimize=True)
            written += 1
        except Exception as e:
            print(f'  SKIP {fname}: {e}')

    print(f'{dst_name}: {written} images written')

print('\nDone.')
