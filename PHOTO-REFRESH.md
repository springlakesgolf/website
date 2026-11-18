# Photo refresh concept (2026-11-17)

Rough first pass using the Rich Nixx Media 2026 photos. Fable 5.2 finishes it.
Branch `claude/photo-refresh-concept`. Only image files changed; no HTML, CSS or copy edits.

## How it was done
- New photos were written over the existing slot files (same filename, same format), so every page picks them up with no markup change. The old files are still on `main`.
- Web size: about 2000 px wide (1600 to 1800 where needed), under 400 KB each, `.webp` slots as WebP and `.jpg` slots as JPEG.
- Originals live on Spring Lakes Media Drive 1 (`E:\Spring Lakes Photos`), mirrored on Drive 2 (F:). Source paths below are relative to that root.
- `tools/build.py` rebuilds from the Mac's `~/Downloads/Marketing & Promotions/springlakes-site`. Carry these swaps into that source's `assets/img`, or a rebuild will put the old photos back.

## Slot map
| Slot file | Pages | New photo (source) | Notes |
|---|---|---|---|
| `hero-aerial.jpg` | home hero, course gallery | Canada Day, Sneak Peak `DJI_20260701162502_0098_D.jpg` | Drone, wide over the property and clubhouse |
| `g18.webp` | home, course gallery | Canada Day, Sneak Peak `DJI_20260701162144_0092_D.jpg` | Drone, island green with clubhouse; alt "Aerial view over Spring Lakes" still fits |
| `golf-aerial.jpg` | golf, course gallery | Canada Day, Sneak Peak `DJI_20260701094719_0014_D.jpg` | Drone, ponds and fairways |
| `g05.webp` | home, golf academy, course gallery | Ryder Cup, Best Of `_RSN5965.jpg` | Golfer chipping |
| `g26.webp` | home, golf camps, course gallery | Ryder Cup, Best Of `RSN06553.jpg` | Bunker and big sky, East Course |
| `g15.webp` | memberships, course gallery | Canada Day, Sneak Peak `_RSN0152.jpg` | Clubhouse over the green with the flag |
| `g04.webp` | contact hero, course gallery | Canada Day, Sneak Peak `_RSN8934.jpg` | Engraved entrance stone (1600 px to stay under 400 KB) |
| `g12.webp` | members, course gallery | Canada Day, Sneak Peak `_RSN9067.jpg` | Group in red and white, Canada Day (1800 px) |
| `g17.webp` | members, course gallery | Ryder Cup, Best Of `_RSN7158.jpg` | Golfer near a bunker |
| `g28.webp` | members, course gallery | Canada Day, Sneak Peak `_RSN9975.jpg` | Swing, finish position |
| `member-leagues.webp` | members (leagues) | Ryder Cup, Best Of `RSN06700.jpg` | Group on a green under a big sky |

Folder shorthand: "Canada Day, Sneak Peak" = `01 By Event\2026-07-01 Canada Day Mens Night\Spring Lakes - Canada Day - Sneak Peak`; "Ryder Cup, Best Of" = `08 Best Of (website and social picks)\2026-08-15 Ryder Cup`.

## Left alone on purpose
- `course-north/east/south.webp`: the drone shots are not tagged by course yet. Only swap once the course in the shot is confirmed (the Ryder Cup was played on the East).
- `g25.webp`: its alt text promises golden evening light; the new sets are midday summer.
- `clubhouse.jpg` (dining page): dining is for members and their guests, so do not add food or patio-dining imagery to public pages. A plain clubhouse exterior is fine if a better one turns up.
- `junior-lesson.jpg`, `member-junior.webp` (golf camps): Junior Summer Camp photos are in `05 Juniors (consent check before public use)`. Confirm photo consent before any junior photo goes on a public page.
- Food shots (`_RSN0276`, `_RSN0308` etc.): members area only, never public dining promotion.
- Course gallery: picks up the swaps above automatically. For the full refresh, pull roughly 30 from `08 Best Of` and `02 Course and Grounds`.

## Do not use
- Anything showing the old flying heron (for example golf cart roofs, `_RSN8947`) or the retired 10 Years badge (check event pin flags such as `_RSN0052` before using them). The current mark is the standing heron.

## Still to come
- Club Championship and Junior Summer Camp galleries are being downloaded and sorted on Drive 1; check their `08 Best Of` folders for more picks.
- Member Guest High-Res is not downloaded (Pic-time charges $500); waiting on Cullen.

## For Fable 5.2
1. Review each swap at desktop and phone widths; check `object-position` on hero crops.
2. Write real `alt` text for slots that have `alt=""` (g05, g26, g15, g04, g17, g12, g28) where the image carries meaning.
3. Carry the final picks into the Mac source folder, rebuild with `tools/build.py`, preview, then merge.
4. House rules for any copy: no em or en dashes, say "our team" not staff names, never publish membership prices, no public dining promotion.
