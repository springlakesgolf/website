# Photo refresh (2026-11-18)

The site now runs on the Rich Nixx Media 2026 photos. Picks and the do-not-use list: `tools/photos/PICKS.md`.

## How it works
- `tools/photos/manifest.py` lists every photo: an id, the original on the photo drive, an optional crop, and its alt text.
- `tools/photos/export.py` turns the originals into web files in `tools/photos/img/` (WebP: 2000 px under 400 KB, 1200 px `-m`, 800 px `-t`). It needs Spring Lakes Media Drive 1 (`E:\Spring Lakes Photos`). The exported files are committed, so nothing else needs the drive.
- `tools/photos/photos.py` puts them on the pages: one photo per image slot (with its alt text and crop position for desktop and phone), the course gallery, and the photo viewer (`tools/photos/gallery.js`).
- `tools/build.py` calls it, so a rebuild on the Mac keeps the new photos even though the June source folder still has the old ones. On the PC, where the June source folder does not exist, `python tools/photos/photos.py` applies the same thing to the built pages.
- Two settings at the top of `photos.py`: `HERO` (home hero A to D) and `GALLERY` (layout A to C).

## To change a photo
1. New photo: add a line to `manifest.py`, then `python tools/photos/export.py`.
2. Point the slot (or the gallery list) at its id in `photos.py`. `--pos` is the crop position on desktop, `--pos-m` on phones.
3. `python tools/photos/photos.py` (PC) or `python3 tools/build.py` (Mac), check the page, commit.

## Slot map
| Page | Slot | Photo id | What it shows |
|---|---|---|---|
| Home | hero | `morning-ponds` (option A) | Morning over two ponds, pines and bunkers, from the air |
| Home | about figure | `island-green` | Island green beside the clubhouse, from the air |
| Home, Golf | East course card | `green-big-sky` | A green on the East Course (Ryder Cup) |
| Home | dining teaser | `golden-fairways` | Golden evening light over fairways and ponds, from the air |
| Home | Academy card | `chip-shot` | Golfer chipping onto a green |
| Home | Junior Golf card | `bunker-blue-sky` | Bunker and fairway, blue sky |
| Golf | hero | `property-wide` | Wide over the property, island green and clubhouse |
| Golf Academy | hero | `bunker-shot` | Bunker shot, sand in the air |
| Junior Golf | hero | `bunker-blue-sky` | Bunker and fairway, blue sky |
| Memberships | hero | `clubhouse-green` | Clubhouse across a green, Canada flag pin |
| Contact | hero | `clubhouse-aerial` | Clubhouse and island green from the air |
| Dining | hero | `clubhouse-fountain` | Clubhouse across the pond and fountain |
| Dining | figure | `clubhouse-gardens` | Clubhouse veranda and gardens |
| Members | hero | `members-putting` | Members putting under a big sky |
| Members | events card, corporate and golf days | `teams-clubhouse` | Both Ryder Cup teams at the clubhouse |
| Members | events card, social celebrations | `banquet-room` | Members in the banquet room (members area only) |
| Members | leagues figure | `handshake-green` | Four players shaking hands on a green |
| Course Gallery | hero | `ponds-wide` | Wide aerial with ponds |
| Course Gallery | 33 photos | see `LAND`, `CLUB`, `PLAY` in `photos.py` | Land first, then the clubhouse, then members at play |

## Kept the old photo, and why
- North and South course cards (`course-north.webp`, `course-south.webp`): the course in each new shot is not confirmed. Swap once Cullen says which course Canada Day Men's Night and the Club Championship were played on.
- Pro portraits on the Golf Academy page: staff headshots are not in the new library.
- Junior Golf page (`camp-2027-flyer.jpg`, `member-junior.webp`, `junior-lesson.jpg`): no new junior photos until photo consent is confirmed. The page hero and the home card use a course photo with no people.

## Rules that still apply
- The standing heron is the only logo. Nothing showing the old flying heron (pin flags, tee markers, signs, cart roofs, the entrance stone emblem) or the 10 Years badge.
- No junior photos on public pages until consent is confirmed. No food, bar or patio dining photos on public pages.
- At most three Canada flag pins in the gallery.
- Alt text: one plain sentence, no dashes, no staff or member names.
- Never commit the photographer's gallery links.

## Still to come
- Member Guest photos are not downloaded yet.
- Drive 2 (F:) has not been mirrored since the Club Championship set was sorted.
