"""
process_sequences.py
Converts Meltdown PNG sequences to subsampled JPEGs for GitHub Pages.
Takes every 2nd frame, converts PNG→JPEG at quality 78.
Output: meltdown/seq/dir1..dir5/ + manifest1..5.json
"""

import os, json, sys
from PIL import Image

SAMPLE_EVERY = 2
JPEG_QUALITY = 78

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_OUT  = os.path.join(BASE_DIR, 'outputs')
DST_SEQ  = os.path.join(BASE_DIR, 'seq')

# Map group number → source dir name (group 1 uses bare 'dir', rest use 'dir2' etc.)
GROUPS = [
    (2, 'dir2', 'manifest2.json'),
    (3, 'dir3', 'manifest3.json'),
    (4, 'dir4', 'manifest4.json'),
    (5, 'dir5', 'manifest5.json'),
]

def pad(n):
    return str(n).zfill(4)

total_written = 0

for g_num, src_dir_name, manifest_name in GROUPS:
    src_dir  = os.path.join(SRC_OUT, src_dir_name)
    dst_dir  = os.path.join(DST_SEQ, f'dir{g_num}')
    src_manifest = os.path.join(SRC_OUT, manifest_name)
    dst_manifest = os.path.join(DST_SEQ, f'manifest{g_num}.json')

    print(f'\n=== Group {g_num}: {src_dir_name} ===')

    with open(src_manifest) as f:
        entries = json.load(f)

    new_manifest = []

    for entry in entries:
        d        = str(entry['dir'])
        frames   = int(entry['frames'])
        src_seq  = os.path.join(src_dir, d)
        dst_seq  = os.path.join(dst_dir, d)
        os.makedirs(dst_seq, exist_ok=True)

        new_frame_count = 0
        for orig_f in range(1, frames + 1, SAMPLE_EVERY):
            src_file = os.path.join(src_seq, pad(orig_f) + '.png')
            if not os.path.exists(src_file):
                continue
            new_frame_count += 1
            dst_file = os.path.join(dst_seq, pad(new_frame_count) + '.jpg')
            try:
                with Image.open(src_file) as img:
                    img = img.convert('RGB')
                    img.save(dst_file, 'JPEG', quality=JPEG_QUALITY, optimize=True)
            except Exception as e:
                print(f'  SKIP {src_file}: {e}')
                new_frame_count -= 1
                continue

        if new_frame_count > 0:
            new_manifest.append({'dir': d, 'frames': new_frame_count})

        total_written += new_frame_count
        sys.stdout.write(f'\r  Seq {d}/{len(entries)} — {total_written} frames written total')
        sys.stdout.flush()

    os.makedirs(DST_SEQ, exist_ok=True)
    with open(dst_manifest, 'w') as f:
        json.dump(new_manifest, f)
    print(f'\n  Wrote {len(new_manifest)} sequences -> {dst_manifest}')

print(f'\nDone. Total frames written: {total_written}')
