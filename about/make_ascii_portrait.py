"""
Regenerate the ASCII portrait map for the About page.

WHAT IT PRODUCES
    A hex string, one digit per grid cell, row-major — paste it into
    ABOUT_ASCII.map in index.html (SECTION "THE ASCII PORTRAIT").
        '0'     = empty cell, no character
        '1'-'f' = a character here, at that weight (1 faint, f solid)

WHY IT IS NOT A STRAIGHT BRIGHTNESS SAMPLE
    The source is a polaroid: a light wall behind a person in a black t-shirt.
    Sampling darkness directly clips the whole shirt to 'f' — a solid slab
    across the bottom half — while the face, which is only a little darker
    than the wall, lands at '1'-'3' and effectively disappears. That is the
    map this script replaces.

    So ink is built from two things instead:
      · TONE, illumination-flattened, so the wall's vignette does not read as
        subject and the shirt stops being a single saturated value; and
      · LOCAL DETAIL, a band-pass of the same image, which is what actually
        carries the eyes, brows, nostrils, moustache, jaw and hat brim.
    Detail is weighted heavily on purpose. The face is the point of the
    picture; the shirt is a shape and only needs to read as mass.

EXACT CELL COUNT
    The About copy has N non-space characters and every one of them parks in
    its own lit cell, so the map must light exactly N cells. Rather than
    threshold by value and hope, the script ranks every cell by ink and keeps
    the top N. Pass --chars to match a rewritten ABOUT_COPY.

WHAT IS ACTUALLY SHIPPED
    The map currently in index.html was produced by:

        python about/make_ascii_portrait.py             --crop 0.15,0.02,0.85,0.76             --tone 1.0 --mid 0.6 --fine 3.0 --cap 0.74 --tgamma 1.1 --clean 0

    Every run writes preview-blocks-<tag>.png and preview-letters-<tag>.png
    beside this file. LOOK AT THE LETTER ONE before pasting anything in: the
    block preview flatters the result badly, because on the page the picture is
    drawn in proportional letters at partial opacity, and tonal differences
    that are obvious as solid squares can vanish entirely as type.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SRC = HERE / "CALDER-PORTRAIT-POLOROID.jpg"

COLS = 54            # grid width, must match ABOUT_ASCII.cols
CELL_ASPECT = 0.6    # cell width / cell height, must match CELL_ASPECT in the page
CHARS = 875          # non-space characters in ABOUT_COPY.lede + body


def find_window(im):
    """The polaroid's image area — the emulsion rectangle inside the white frame.

    A bounding box of "anything not white" is not enough: the scan has dust and
    soft edges out on the paper, and one stray dark pixel in a corner drags the
    box out to the full scan. So a row only counts as part of the photo if a
    real FRACTION of it is non-white, which noise can never satisfy.
    """
    g = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    ink = g < 0.88
    rows = np.where(ink.mean(axis=1) > 0.35)[0]
    cols = np.where(ink.mean(axis=0) > 0.35)[0]
    if not len(rows) or not len(cols):
        return (0, 0, im.width, im.height)
    pad = 5                              # step inside the emulsion's soft edge
    return (int(cols[0]) + pad, int(rows[0]) + pad,
            int(cols[-1]) - pad, int(rows[-1]) - pad)


def build_ink(im, tone_w, mid_w, fine_w, gamma, cap, tgamma=0.42):
    """Per-pixel ink, 0..1, from three layers.

    MEASURED, because it explains every weight below: in this photograph the
    wall reads 0.666 and the forehead reads 0.640. The face and the background
    are the SAME TONE. No brightness curve can separate them, which is why both
    the original map and a straight flatten leave a hole where the head is and
    draw only the hair around it.

    So the face is drawn the way an etching draws one — by its features:

      TONE   flattened against a very wide blur, so only the slow vignette is
             divided out. Carries the shirt and the hat: the masses.
      MID    band-pass at head scale. Carries the silhouette — hairline, jaw,
             shoulders — the edges that say where a person stops.
      FINE   band-pass at feature scale. Carries the eyes, brows, nostrils,
             moustache, lips and the shadow under the cheekbone. This is the
             layer that makes it recognisably a face rather than a shape, and
             it is why `fine` is weighted as heavily as the tone.

    Both bands are clipped at zero: a band-pass is signed, and the negative
    half is where something is LIGHTER than its surroundings — catchlights,
    the bright edge of the hat. Letting that through would punch holes in the
    middle of features.
    """
    g = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(0.5)),
                   dtype=np.float32) / 255.0

    def blur(a, sigma):
        return np.asarray(
            Image.fromarray((a * 255).clip(0, 255).astype(np.uint8))
                 .filter(ImageFilter.GaussianBlur(max(sigma, 0.4))),
            dtype=np.float32) / 255.0

    def norm(a):
        m = float(a.max())
        return a / m if m > 1e-6 else a

    w = g.shape[1]

    # THE WALL, MODELLED. A blurred copy of the picture is no good as a
    # reference — blur the face and you get the face back, so the face cancels
    # itself out and vanishes. What is wanted is "how bright would the wall be
    # here if he were not standing in front of it", and that is a local MAXIMUM
    # taken over a window wider than his head: inside the head the window still
    # reaches out to wall on one side or the other. Computed small and scaled
    # back up, because the answer is smooth by construction and a max filter at
    # full resolution would be minutes of work for the same numbers.
    small = Image.fromarray((g * 255).astype(np.uint8)).resize(
        (180, max(2, int(180 * g.shape[0] / w))), Image.BILINEAR)
    k = int(small.width * 0.55) | 1
    wall = small.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.GaussianBlur(9))
    wall = np.asarray(wall.resize((w, g.shape[0]), Image.BICUBIC),
                      dtype=np.float32) / 255.0

    # Everything darker than the wall is subject. The face clears it by only
    # ~0.03 against the shirt's ~0.5, so the difference is gamma-expanded hard:
    # without that the skin rounds to nothing and the head is a hole again.
    tone = np.clip(wall - g, 0.0, None)
    tone = norm(tone) ** tgamma
    # The shirt is a large, evenly lit, information-free mass. Left uncapped it
    # outranks every facial feature and takes most of the cells for itself.
    tone = norm(np.minimum(tone, cap))

    mid  = norm(np.clip(blur(g, w * 0.090) - blur(g, w * 0.018), 0.0, None))
    fine = norm(np.clip(blur(g, w * 0.028) - blur(g, w * 0.004), 0.0, None))

    ink = tone_w * tone + mid_w * mid + fine_w * fine

    # The emulsion darkens for a few pixels at its own edge, and every band-pass
    # reads that edge as a feature — which is where the stray marks floating out
    # in the empty wall come from. Fade the outer margin to nothing.
    yy = np.linspace(0, 1, ink.shape[0])[:, None]
    xx = np.linspace(0, 1, ink.shape[1])[None, :]
    m = 0.075
    edge = (np.clip(np.minimum(xx, 1 - xx) / m, 0, 1) *
            np.clip(np.minimum(yy, 1 - yy) / m, 0, 1))
    ink = ink * edge
    p2, p99 = np.percentile(ink, [2, 99.3])
    ink = np.clip((ink - p2) / max(p99 - p2, 1e-6), 0.0, 1.0)
    return ink ** gamma


def sample(ink, cols, rows):
    """Average the ink over each grid cell."""
    h, w = ink.shape
    out = np.zeros((rows, cols), dtype=np.float32)
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, cols + 1).astype(int)
    for r in range(rows):
        for c in range(cols):
            box = ink[ys[r]:max(ys[r + 1], ys[r] + 1),
                      xs[c]:max(xs[c + 1], xs[c] + 1)]
            out[r, c] = box.mean() if box.size else 0.0
    return out


def quantise(cell, chars, mode, curve, clean):
    """Keep the `chars` inkiest cells, spread them over 1..15, zero the rest.

    RANK spreads the lit cells evenly across all fifteen weights. It guarantees
    the full range is used, but it also gives the shirt — hundreds of cells all
    within a hair of each other — the same share of the top weights as the
    features, which is exactly how the face ends up looking flat.

    VALUE keeps the real distances between cells, so a feature that is genuinely
    darker than the cheek beside it renders genuinely heavier. `curve` < 1 lifts
    the middle of that range so the mid-tones do not collapse into '1'-'3'.
    """
    flat = cell.flatten()
    n = min(chars, flat.size)
    keep = np.argsort(flat)[::-1][:n]
    mask = np.zeros_like(flat, dtype=bool)
    mask[keep] = True
    if clean:
        mask = despeckle(cell, mask.reshape(cell.shape), clean).flatten()

    vals = flat[mask]
    lo, hi = float(vals.min()), float(vals.max())
    if mode == "rank":
        order = np.argsort(np.argsort(vals))
        lvl = 1 + np.floor(order / max(len(vals), 1) * 15).astype(int)
    else:
        t = (vals - lo) / max(hi - lo, 1e-6)
        lvl = 1 + np.round((t ** curve) * 14).astype(int)
    lvl = np.clip(lvl, 1, 15)

    out = np.zeros_like(flat, dtype=int)
    out[mask] = lvl
    return out.reshape(cell.shape), lo, hi


def despeckle(cell, mask, rounds):
    """Trade lonely cells out in the wall for crowded ones on the subject.

    The top-N cut is taken per cell with no regard for its neighbours, so a few
    grains of scan noise out on the empty wall always outrank the faintest real
    cells on the shoulder. One lit cell alone in a field of blue does not read
    as tone — it reads as a mistake. Each round removes the faintest lit cells
    that have almost no lit neighbours and re-spends exactly that many on the
    inkiest unlit cells that have plenty, so the count never changes.
    """
    h, w = cell.shape
    for _ in range(rounds):
        pad = np.pad(mask, 1)
        n = sum(pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - mask

        lonely = np.argwhere(mask & (n <= 1))
        # 4..6 lit neighbours, NOT 7-8: a cell hemmed in on every side is an
        # interior hole, and the interior holes here are the eye sockets and the
        # shadow under the lip. Filling those is precisely how the face goes
        # back to being a flat oval. Only edges get thickened.
        crowd  = np.argwhere(~mask & (n >= 4) & (n <= 6))
        if not len(lonely) or not len(crowd):
            break
        lonely = sorted(lonely.tolist(), key=lambda p: cell[p[0], p[1]])
        crowd  = sorted(crowd.tolist(), key=lambda p: -cell[p[0], p[1]])
        k = min(len(lonely), len(crowd))
        for (r, c) in lonely[:k]:
            mask[r, c] = False
        for (r, c) in crowd[:k]:
            mask[r, c] = True
    return mask


def trim(grid):
    """Drop all-empty rows top and bottom — they only push the face off-centre."""
    lit = (grid > 0).any(axis=1)
    if not lit.any():
        return grid, 0, 0
    top = int(np.argmax(lit))
    bot = int(len(lit) - np.argmax(lit[::-1]))
    return grid[top:bot], top, len(lit) - bot


def preview_blocks(grid, path, cell=14):
    """What the grid looks like as tone: white cells on the About page blue."""
    rows, cols = grid.shape
    w, h = int(cols * cell * CELL_ASPECT), rows * cell
    im = Image.new("RGB", (w, h), (0, 0, 255))
    d = ImageDraw.Draw(im)
    cw = cell * CELL_ASPECT
    for r in range(rows):
        for c in range(cols):
            v = grid[r, c]
            if not v:
                continue
            a = 0.18 + 0.82 * (v / 15.0)        # the page's own opacity curve
            g = int(255 * a)
            d.rectangle([c * cw + cw * 0.12, r * cell + cell * 0.12,
                         (c + 1) * cw - cw * 0.12, (r + 1) * cell - cell * 0.12],
                        fill=(g, g, 255))
    im.save(path)


def preview_letters(grid, path, text, cell=22):
    """Closer to the real thing: the copy's own letters, in reading order."""
    rows, cols = grid.shape
    w, h = int(cols * cell * CELL_ASPECT), rows * cell
    im = Image.new("RGB", (w, h), (0, 0, 255))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", int(cell * 0.8))
    except OSError:
        font = ImageFont.load_default(size=int(cell * 0.8))
    letters = [ch for ch in text if not ch.isspace()]
    cw = cell * CELL_ASPECT
    i = 0
    for r in range(rows):
        for c in range(cols):
            v = grid[r, c]
            if not v:
                continue
            ch = letters[i] if i < len(letters) else "·"
            i += 1
            a = 0.18 + 0.82 * (v / 15.0)
            g = int(255 * a)
            d.text((c * cw, r * cell), ch, fill=(g, g, 255), font=font)
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", type=int, default=CHARS)
    ap.add_argument("--tone", type=float, default=1.0, help="weight of the masses")
    ap.add_argument("--mid",  type=float, default=0.85, help="weight of the silhouette")
    ap.add_argument("--fine", type=float, default=1.25, help="weight of the features")
    ap.add_argument("--cap",  type=float, default=0.62,
                    help="ceiling on tone, so the shirt cannot take every cell")
    ap.add_argument("--gamma", type=float, default=0.9,
                    help="<1 lifts midtones, >1 deepens them")
    ap.add_argument("--crop", default="0,0,1,1",
                    help="l,t,r,b as fractions of the polaroid window. Cropping "
                         "in spends the same 875 cells on less picture, which is "
                         "the only real way to buy detail in the face.")
    ap.add_argument("--tgamma", type=float, default=0.42,
                    help="how hard the wall-subtracted tone is expanded")
    ap.add_argument("--quant", choices=("rank", "value"), default="value")
    ap.add_argument("--curve", type=float, default=0.75,
                    help="value-quantiser curve; <1 lifts the mid weights")
    ap.add_argument("--clean", type=int, default=2,
                    help="despeckle rounds; 0 to keep every stray cell")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    if not SRC.exists():
        sys.exit(f"source not found: {SRC}")

    im = Image.open(SRC)
    box = find_window(im)
    fl, ft, fr, fb = [float(v) for v in args.crop.split(",")]
    bw, bh = box[2] - box[0], box[3] - box[1]
    box = (box[0] + int(bw * fl), box[1] + int(bh * ft),
           box[0] + int(bw * fr), box[1] + int(bh * fb))
    crop = im.crop(box)
    cw, ch = crop.size

    rows = int(round(COLS * CELL_ASPECT * ch / cw))
    ink = build_ink(crop, args.tone, args.mid, args.fine, args.gamma,
                    args.cap, args.tgamma)
    cells = sample(ink, COLS, rows)
    grid, lo, hi = quantise(cells, args.chars, args.quant, args.curve,
                            args.clean)
    grid, cut_top, cut_bot = trim(grid)

    tag = args.tag or "out"
    preview_blocks(grid, HERE / f"preview-blocks-{tag}.png")
    text = "the quick brown fox jumps over the lazy dog " * 40
    preview_letters(grid, HERE / f"preview-letters-{tag}.png", text)

    lines = ["".join(f"{v:x}" for v in row) for row in grid]
    print(f"window   : {box}  ({cw}x{ch})")
    print(f"sampled  : {COLS} x {rows}, trimmed {cut_top} rows above / "
          f"{cut_bot} below -> {grid.shape[0]} rows")
    print(f"lit cells: {int((grid > 0).sum())} (target {args.chars})")
    print(f"preview  : preview-blocks-{tag}.png / preview-letters-{tag}.png")
    print()
    print(f"  cols: {COLS},")
    print(f"  rows: {grid.shape[0]},")
    print("  map:")
    for i, ln in enumerate(lines):
        end = " +" if i < len(lines) - 1 else " +"
        print(f"    '{ln}'{end}")
    print("    ''")


if __name__ == "__main__":
    main()
