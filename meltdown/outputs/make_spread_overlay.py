import numpy as np
from PIL import Image
from pathlib import Path

SPREAD_PDF_RENDER = Path(r"C:\Users\Calder S. Anderson\Downloads\meltdown process book spread.pdf")
SUBFOLDER         = Path(r"C:\Users\Calder S. Anderson\Desktop\PARSONS SENIOR YEAR\STUDIO\stabilityaiturboxd_pipeline\outputs\dir2\35")
OUTPUT            = Path(r"C:\Users\Calder S. Anderson\Desktop\PARSONS SENIOR YEAR\STUDIO\stabilityaiturboxd_pipeline\outputs\process_spread_overlay.png")
DPI               = 300

# ── 1. Re-render spread to get exact pixel dimensions ───────────────────────
import fitz
doc    = fitz.open(str(SPREAD_PDF_RENDER))
page   = doc[0]
mat    = fitz.Matrix(DPI / 72, DPI / 72)
pix    = page.get_pixmap(matrix=mat)
W, H   = pix.width, pix.height          # 5100 x 3300
print(f"Spread: {W} x {H} px  ({W/DPI:.2f}\" x {H/DPI:.2f}\")")

# ── 2. Load sequence (31 images; duplicate last to fill 32 cells) ────────────
images = sorted(SUBFOLDER.glob("*.png"), key=lambda p: int(p.stem))
n      = len(images)
print(f"Found {n} images in {SUBFOLDER.name}")
if n == 31:
    images = list(images) + [images[-1]]   # duplicate final frame
    print("  31 images: duplicating last frame to complete 32-cell grid")
elif n != 32:
    raise ValueError(f"Expected 31 or 32 images, got {n}")

# ── 3. Compute grid — 8 cols x 4 rows of SQUARE cells ───────────────────────
COLS, ROWS = 8, 4                        # 8 * 4 = 32
CELL       = W // COLS                   # 637 px  (square, 1:1)
BLOCK_W    = COLS * CELL                 # 5096 px
BLOCK_H    = ROWS * CELL                 # 2548 px
# Block anchored to top-left of spread; transparent strip below
print(f"Grid: {COLS}x{ROWS}  |  cell: {CELL}px  |  block: {BLOCK_W}x{BLOCK_H}px")

# ── 4. Build RGBA canvas — transparent everywhere ────────────────────────────
out = Image.new("RGBA", (W, H), (0, 0, 0, 0))

for idx, img_path in enumerate(images):
    row = idx // COLS
    col = idx % COLS
    x0  = col * CELL
    y0  = row * CELL

    with Image.open(img_path) as img:
        img = img.convert("RGBA").resize((CELL, CELL), Image.LANCZOS)

    out.paste(img, (x0, y0))             # fully opaque — no masking
    print(f"  [{idx+1:02d}/32] col={col} row={row}  pos=({x0},{y0})")

# ── 5. Save ───────────────────────────────────────────────────────────────────
out.save(str(OUTPUT), dpi=(DPI, DPI))
print(f"\nSaved: {OUTPUT}")
print(f"Block covers top {BLOCK_H/H*100:.0f}% of the spread ({BLOCK_W/DPI:.2f}\" x {BLOCK_H/DPI:.2f}\")")
