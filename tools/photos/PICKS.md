# Final picks and build plan (2026-11-18, Fable 5.2 session 1)

Session 1 reviewed the whole library on contact sheets and chose the photos. Nothing is exported or built yet. Session 2 builds from this file. Read `PHOTO-REFRESH.md` and `PRODUCT.md` first.

## Facts found
- The June source folder (`~/Downloads/Marketing & Promotions/springlakes-site`) is on the Mac only. It is not on the PC, so `tools/build.py` cannot run on the PC.
- Club Championship (1178 photos) was never sorted. It is sorted and indexed now (2026-11-18); check `08 Best Of\2026-07-11 Club Championship` for a few more gallery picks. Its evening drone set (DJI_20260712...) is the only golden hour light in the library.
- Windows Python needs `E:/Spring Lakes Photos/...` paths, not `/e/...`.
- The image guard hook blocks reading images over about 0.35 MB. `tools/photos/sheet.py` makes contact sheets that pass (`python sheet.py <name> <cols> <thumb px> <per page> <list file>`, 6 columns at 250 px and 30 per page works); `tools/photos/find.py <names file> <out list>` turns file stems into full paths.
- `tools/design-options/` is gitignored: put option mockups there.
- `.claude/launch.json` points at the Mac path. Add a PC entry (for example `python -m http.server 8743`) rather than changing the Mac one.
- Headless screenshots: `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --screenshot=out.png --window-size=1440,900 <url>`.
- Bash heredocs with apostrophes in the body fail in this shell. Use the Write tool for files.

## Do not use (old flying heron is readable)
- Regular pin flags (white flag, black heron): `_RSN0363 _RSN0403 _RSN9950 _RSN9840 _RSN9958 _RSN9874 RSN07366 RSN07375 RSN07376 RSN08094` and any other close pin flag that is not a Canada flag.
- Heron shaped tee markers up close: `RSN07006 RSN07008 RSN07009 _RSN0204 _RSN0209`.
- Signs and wall art: `_RSN0421 _RSN0423 _RSN0424 _RSN9584 _RSN9585 _RSN9587 _RSN9556 _RSN0065 _RSN5888 _RSN5890 RSN06144`.
- Wide entrance stone shots (the stone carries the old emblem): `_RSN8933 _RSN8934 _RSN0428 _RSN0430 _RSN0432 _RSN0434 _RSN5871 to _RSN5878`. The tight lettering crops `_RSN0441` and `_RSN0437` show only "SPRING LAKES GOLF CLUB" and are fine.
- Close cart shots: `_RSN5939 _RSN9316 _RSN9317 RSN06103 _RSN8937 _RSN8939`.
- All of `05 Juniors`, including the camp volleyball, barn and ice cream truck sets. All of `06 Food and Drink`. Patio and bar scenes (`_RSN9387 _RSN9390 _RSN9458 to _RSN9467`).
- Canada flag pins are fine. Use at most three in the gallery so it does not read as a Canada Day album.

## Checked clean at 760 px (no old logo, no badge)
`_RSN0417 RSN06700 RSN06834 RSN06108 _RSN9143 _RSN8959 _RSN9469 RSN06336 _RSN9302 RSN06409 _RSN8579 _RSN0441 _RSN0168 RSN06553 _RSN5965 _RSN0096 _RSN5979 _RSN9724`

Not yet checked up close: the drone shots (fine at thumbnail size, no logos expected), `_RSN9900 _RSN0009 _RSN0120 _RSN0152 _RSN0355 _RSN9149 _RSN5992 RSN07908 _RSN0419`.

## Slot picks
Source stems. "CD" = Canada Day, "RC" = Ryder Cup, "CC" = Club Championship.

| Slot | Page | Pick | What it shows | Notes |
|---|---|---|---|---|
| Home hero | home | options below | | show options first |
| About figure (square) | home | `DJI_20260701162144_0092_D` CD | island green beside the clubhouse, from the air | |
| Dining teaser (5:4) | home | `DJI_20260712202841_0116_D` CC | golden evening light over the fairways, from the air | keeps the "golden evening light" alt honest; no food or patio |
| Academy card | home | `_RSN5965` RC | golfer chipping onto a green | |
| Junior Golf card and Junior Golf hero | home, golf-camps | `_RSN0355` CD | bunker and fairway under a blue summer sky | no junior photos until consent |
| Course card East | home, golf | `RSN06834` RC | green under a big sky | Ryder Cup was played on the East |
| Course cards North, South | home, golf | keep old | | the course in each new shot is not confirmed |
| Golf hero | golf | `DJI_20260701162502_0098_D` CD | wide over the property, island green and clubhouse | if this becomes the home hero, use `DJI_20260701094719_0014_D` here |
| Academy hero | golf-academy | `RSN06108` RC | bunker shot, sand in the air | crop about 7% off the right (blurred cart frame) |
| Pro portraits | golf-academy | keep old | | staff headshots, not in the new library |
| Camp flyer, `member-junior.webp`, `junior-lesson.jpg` | golf-camps | keep old | | consent not confirmed for new junior photos |
| Memberships hero | memberships | `_RSN0152` CD | clubhouse across the green, Canada flag pin | |
| Contact hero | contact-us | `DJI_20260701163128_0113_D` CD | drone over the clubhouse and island green | Cullen asked for a drone shot here |
| Dining hero | food-beverage | `_RSN0096` CD | clubhouse across the pond and fountain | exterior only |
| Dining figure (`clubhouse.jpg`) | food-beverage | `_RSN5979` RC | clubhouse veranda and gardens | exterior only |
| Members hero | members | `RSN06700` RC | members putting under a big sky | |
| Events card: corporate and golf days | members | `RSN06409` RC | both Ryder Cup teams in front of the clubhouse | crop the bottom quarter (pavement) |
| Events card: social celebrations | members | `_RSN8579` RC | members at round tables in the banquet room | members area only; glasses on tables, so never on a public page |
| Leagues figure (5:4) | members | `_RSN9302` CD | four players shaking hands on a green | |
| Gallery hero | course-gallery | `DJI_20260712203312_0126_D` CC | wide aerial with ponds | or `DJI_20260701145025_0086_D` (ponds from straight above) |

## Home hero options to show (each at desktop 1440x900 and phone 390x844)
- A, recommended: `DJI_20260701094719_0014_D` CD. Morning over two ponds, pines and bunkers, horizon at the top. All land, no buildings, and the blue and green hold up under the navy scrim.
- B: `DJI_20260712202345_0107_D` CC. Golden evening, sun flare, bunkers. Road on the right edge: crop it or push object-position left.
- C: `DJI_20260701162502_0098_D` CD. Wide over the property with the island green and clubhouse (the current concept).
- D: `DJI_20260712203621_0131_D` CC. Dusk, low over a fairway and bunker, clubhouse in the trees. Road at the bottom right: crop it out.

Keep the scrim, heron mark, title and buttons exactly as they are.

## Course gallery layout options to show
- A: the current masonry columns, refined (natural crops, mixed orientations).
- B: editorial grid, even 3:2 tiles in three columns with a large feature tile every few rows.
- C: three quiet sections, "The Land", "The Clubhouse", "Members at Play", each with a feature image and a grid.

All three: the grid loads 800 px thumbs, a tap opens the 2000 px photo in a simple keyboard friendly lightbox with the alt text as caption; without JavaScript the link still opens the photo.

## Gallery photos (about 32, land first)
`DJI_20260701094719_0014_D` morning ponds, `DJI_20260701162144_0092_D` island green, `_RSN0417` storm clouds over a fairway, `RSN06553` bunker and big sky, `_RSN9900` pond and pines, `DJI_20260701145025_0086_D` ponds from above, `_RSN0120` Canada flag on a green by the pond, `RSN06834` green under a big sky, `_RSN0168` golfers reflected in a pond, `DJI_20260712202841_0116_D` golden aerial, `_RSN0009` fescue, `RSN07908` swan on a pond, `_RSN5979` clubhouse gardens, `_RSN5992` heron sculpture in the flower garden, `_RSN9724` two white chairs under a spruce, `_RSN0355` bunker and blue sky, `DJI_20260712192400_0105_D` figure eight pond from above (crop the road off the bottom), `_RSN0152` clubhouse over the green, `RSN06108` bunker shot, `_RSN9143` tee shot framed by a maple, `_RSN8959` foursome on the tee, `_RSN9469` two members walking with their bags, `RSN06336` driver swing, `_RSN9302` handshake on the green, `RSN06700` members putting, `_RSN0419` sun rays through storm cloud (portrait), `_RSN0441` engraved stone lettering, `DJI_20260712202345_0107_D` golden sun flare, `_RSN0096` clubhouse and fountain, `_RSN9149` green and bunker, `DJI_20260712203621_0131_D` dusk, `RSN06409` both teams at the clubhouse. Add two or three from the Club Championship Best Of if they beat these.

The gallery intro says "through the seasons"; every new photo is summer 2026, so change it to "photographed through the 2026 season".

## Build plan (rebuild safe without the Mac folder)
The repo holds the photos, so a rebuild on the Mac keeps them even though the Mac source folder still has the old files. This replaces "carry the picks into the Mac source folder", which cannot be done from the PC.

1. `tools/photos/export.py`: reads a manifest (id, source stem, optional crop box), writes WebP into `tools/photos/img/`: full 2000 px wide under 400 KB (step quality down until it fits), `-m` 1200 px for cards and figures, `-t` 800 px for gallery tiles.
2. `tools/photos/photos.py`: `install(OUT)` copies `tools/photos/img/*` into `assets/img/`; `apply(slug, html)` rewrites each slot's `<img>` (new src, real alt text, `style="--pos:..;--pos-m:.."`, and `data-photo="<slot id>"` so it can run twice) and replaces the gallery block between `<!--gallery-->` markers (the first run matches the original `<div class="gallery reveal">...</div>`); `CSS` adds `object-position:var(--pos,center)` with a phone override under 700 px, plus the gallery and lightbox styles; `prune(OUT)` drops images no page references.
3. `tools/build.py`: call `photos.install` after the assets copy, `photos.apply` right after `edit(f, s)`, append `photos.CSS`, call `photos.prune` at the end. Slots are matched by the old filename in the built page (for example `g17.webp` on `members`), and several pages reuse one old file, so key each slot on page plus filename plus occurrence.
4. `python tools/photos/photos.py` run on its own applies the same thing to the built pages in this checkout (needed on the PC). Move unreferenced old images to `~/_to_delete/`, never `rm`.
5. Alt text: one plain sentence per meaningful image, no dashes, no staff or member names. Decorative repeats keep `alt=""`.

## Still to do, in order
1. Export the picks; view each hero at desktop and phone crops and set `--pos` and `--pos-m`.
2. Build the hero options and gallery layout options in `tools/design-options/`, screenshot them, send Cullen the images, and ask with one popup: hero pick, gallery pick, and whether to merge once those are in.
3. Build `photos.py`, wire `build.py`, apply to the pages, prune old images.
4. Check every page in the browser pane at desktop and phone widths; fix crops.
5. One `reviewer` pass against this file and `PRODUCT.md`. Grep the built pages for em and en dashes, "enquiry", prices, staff names in new alt text, and Pic-time links.
6. Update the slot table in `PHOTO-REFRESH.md` to the final map, commit, push, merge to main on Cullen's approval, and report the preview link (springlakesgolf.github.io/website).
