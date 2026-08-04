# index_media

Images for the **Index** view rows on the homepage. Filled in from the `HERO
IMAGES/` folder — each project's row cross-fades through 3 stills on hover
(and auto-cycles while on screen on phones).

If a file ever goes missing, its row falls back to a neutral grey plate with
the project title ghosted in — not a broken-image icon.

## Current files

| Row | Project                      | Files                     | Cell shape |
|-----|-------------------------------|---------------------------|------------|
| 01  | Login Magazine                | `login-01/02/03.jpg`      | 3:2 (matches its landscape spreads) |
| 02  | Meltdown                      | `meltdown-01/02/03.jpg`   | 1:1 (2 of 3 photos are square) |
| 03  | ULTRANET                      | `ultranet-01/02/03.jpg`   | 3:2 |
| 04  | Are You Coming to The Party?  | `aycttp-01/02/03.jpg`     | 3:2 (matches its 2 landscape spreads; the cover is the odd one out) |
| 05  | As Above So Below             | `asb-01/02/03.jpg`        | 16:9 |

`graphic-01/02/03.jpg` still exist here, but **Graphic Work is currently
excluded from the Index list** (it still appears as a Network node) — see
`idxSortedProjects()` in `index.html`. Left in place in case it's re-added.

Media never crops: `.index-media` uses `object-fit: contain`, so a photo
that doesn't match its row's cell shape just gets shrunk to fit inside it in
full, rather than being cut off. The cell shape column above is chosen to
match whichever ratio most of that row's photos actually are, so as little
of the box goes to grey padding as possible.

All resized from `HERO IMAGES/` (23 MB of originals → 3.0 MB here) — longest
edge capped at 1600px, JPEG quality 82, EXIF rotation applied, transparency
flattened to white. `-01` is the still that's always visible; `-02`/`-03`
cross-fade in on hover. (`meltdown-03.jpg` is the one exception — pulled from
`meltdown/PROJECT IMAGES/bsfcbsxdv.jpg` instead, since the folder's own
`contact_sheet.png` reads as illegible noise once scaled down to hero size.)

## To swap a picture

Replace the file in place (same name) or point `index.html` at a new one —
search for `INDEX CONTENT — DROP YOUR TEXT AND IMAGES HERE`, each project's
`media:` array lists its three paths.

## Rules

- **Lowercase, hyphens, no spaces.** The live site runs on Linux, which is
  case-sensitive. `My Photo.JPG` works on your laptop and 404s on
  calder-anderson.com.
- **~1600px on the long edge, under ~350 KB.** Nothing is cropped — the whole
  image always shows — but a photo whose shape doesn't match its cell will
  get letterboxed (grey padding on two sides), so still aim for something
  close to the cell shape above where you can.
- Don't point rows at the raw project folders (`meltdown/PROJECT IMAGES/`,
  `graphic_work/project_images/`, etc.) — those are original-resolution masters,
  some tens of MB each.

## Changing the shapes, order or wording

Everything is in one block in `index.html` — search for:

```
INDEX CONTENT — DROP YOUR TEXT AND IMAGES HERE
```

That block holds each row's description, its `aspect` (cell shape) and its list
of images. It also documents how to use a **video** instead of stills.
