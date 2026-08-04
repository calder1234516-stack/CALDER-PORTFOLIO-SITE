import os
import re
import math
from PIL import Image
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\Calder S. Anderson\Desktop\PARSONS SENIOR YEAR\STUDIO\stabilityaiturboxd_pipeline\outputs")
DPI = 300
# Landscape 17 x 11 inches
SHEET_W = int(17 * DPI)  # 5100 px
SHEET_H = int(11 * DPI)  # 3300 px


def sort_key(path: Path):
    """Sort by (top-level dir number, subdir number, file number) numerically."""
    parts = path.relative_to(OUTPUT_DIR).parts
    # parts[0] = 'dir', 'dir2', etc.
    dir_name = parts[0]
    m = re.match(r"dir(\d*)", dir_name)
    dir_num = int(m.group(1)) if m and m.group(1) else 1

    subdir_num = int(parts[1]) if len(parts) > 2 else 0

    stem = Path(parts[-1]).stem
    file_num = int(re.sub(r"\D", "", stem)) if re.search(r"\d", stem) else 0

    return (dir_num, subdir_num, file_num)


print("Collecting images...")
all_images = sorted(
    [p for p in OUTPUT_DIR.rglob("*.png")],
    key=sort_key,
)
n = len(all_images)
print(f"Found {n} images")

# Calculate grid so thumbnails are square-ish and fill the landscape sheet
# cols / rows ≈ SHEET_W / SHEET_H  →  cols ≈ sqrt(n * W / H)
cols = math.ceil(math.sqrt(n * SHEET_W / SHEET_H))
rows = math.ceil(n / cols)
thumb = min(SHEET_W // cols, SHEET_H // rows)

print(f"Grid: {cols} cols x {rows} rows, {thumb}px thumbnails")
print(f"Sheet: {SHEET_W} x {SHEET_H} px  ({SHEET_W/DPI:.1f}\" x {SHEET_H/DPI:.1f}\" at {DPI} DPI)")

sheet = Image.new("RGB", (SHEET_W, SHEET_H), (0, 0, 0))

for i, img_path in enumerate(all_images):
    col = i % cols
    row = i // cols
    x = col * thumb
    y = row * thumb
    try:
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            img.thumbnail((thumb, thumb), Image.LANCZOS)
            sheet.paste(img, (x, y))
    except Exception as e:
        print(f"  Error on {img_path.name}: {e}")

    if i % 1000 == 0:
        print(f"  {i}/{n} ({100*i//n}%)")

out_path = OUTPUT_DIR / "contact_sheet.png"
print(f"Saving to {out_path} ...")
sheet.save(str(out_path), dpi=(DPI, DPI))
print(f"Done. Saved {out_path}")
