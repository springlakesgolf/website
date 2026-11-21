# Photo refresh (2026-11-18)

The site now runs on the Rich Nixx Media 2026 photos. Picks and the do-not-use list: `tools/photos/PICKS.md`.

## How it works
- `tools/photos/manifest.py` lists every photo: an id, the original on the photo drive, an optional crop, and its alt text.
- `tools/photos/export.py` turns the originals into web files in `tools/photos/img/` (WebP: 2000 px under 400 KB, 1200 px `-m`, 800 px `-t`). It needs Spring Lakes Media Drive 1 (`E:\Spring Lakes Photos`). The exported files are committed, so nothing else needs the drive.
- `tools/photos/photos.py` puts them on the pages: one photo per image slot (with its alt text and crop position for desktop and phone), the course gallery, and the photo viewer (`tools/photos/gallery.js`).
- `tools/build.py` calls it, so a rebuild on the Mac keeps the new photos even though the June source folder still has the old ones. On the PC, where the June source folder does not exist, `python tools/photos/photos.py` applies the same thing to the built pages.
- Two settings at the top of `photos.py`: `HERO` (home hero: O the original, or A to E) and `GALLERY` (layout A to C).

## Cullen's picks (2026-11-18)
- Home hero: he asked for a bigger property shot like the original, and to keep the original if no new photo beat it. None did (the two widest new shots have a road and ploughed field, or the parking lot, in frame), so `HERO = "O"` keeps the original autumn aerial (`tools/photos/img/hero-aerial.jpg`). The closest new shot is exported as `property-sky` (option E) if he wants to switch.
- Gallery: layout C, three sections.
- Courses: Canada Day Men's Night and the Club Championship were both played on the East. The Canada Day set also has photos from all three courses, so no photo is confirmed as North or South.

## To change a photo
1. New photo: add a line to `manifest.py`, then `python tools/photos/export.py`.
2. Point the slot (or the gallery list) at its id in `photos.py`. `--pos` is the crop position on desktop, `--pos-m` on phones.
3. `python tools/photos/photos.py` (PC) or `python3 tools/build.py` (Mac), check the page, commit.

## Slot map
| Page | Slot | Photo id | What it shows |
|---|---|---|---|
| Home | hero | `hero-aerial.jpg` (option O, the original) | Autumn aerial with the island green, ponds and fairways |
| Home | about figure | `island-green` | Island green beside the clubhouse, from the air |
| Home, Golf | East course card | `green-big-sky` | A green on the East Course (Ryder Cup) |
| Home | clubhouse and dining teaser | `clubhouse-path` | A couple walking up the garden path to the clubhouse veranda |
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

## Photo matches the words (checked 2026-11-18, at Cullen's request)
Every slot was checked against the heading and copy beside it and against its own alt text, at desktop and phone crops.
- Changed: the home clubhouse and dining teaser showed fairways from the air; it now shows the clubhouse (`clubhouse-path`). In the gallery, the team photo moved from The Clubhouse to Members at Play, and `clubhouse-path` joined The Clubhouse (the bunker shot left the gallery to keep the rows even; it is still the Golf Academy hero).
- Closest available, not a true match: the Golf Academy card and hero show members playing short game shots, because the library has no lesson, range or fitting photos. The Junior Golf card and hero show a bunker with no people, because new junior photos wait on consent.

## Kept the old photo, and why
- Home hero (`hero-aerial.jpg`): Cullen's pick, see above.
- North and South course cards (`course-north.webp`, `course-south.webp`): both events were on the East, so no new photo is confirmed as North or South. Swap when a photo is known to show that course.
- Pro portraits on the Golf Academy page: staff headshots are not in the new library.
- Junior Golf page (`camp-2027-flyer.jpg`, `member-junior.webp`, `junior-lesson.jpg`): no new junior photos until photo consent is confirmed. The page hero and the home card use a course photo with no people.

## Photo picker (staff edit mode, 2026-11-21)
In "Suggest an edit" mode, tapping a photo (or the background of a page's top banner) opens a panel of other photos that fit that spot. Picking one and pressing "Use this photo" adds a row to the Edits tab: Section `Photo pick: <slot>`, Current text `Photo: <file there now>`, Requested change `Use photo: sl26-<id>.webp (photo id <id>)` plus any note. The staff-edits Action never sends these to Claude; it marks them Needs Cullen with the slot and photo id.
- To apply a pick: in `tools/photos/photos.py` point that slot at the photo id (slot ids are `<page or home>:<old file stem>`, the `data-photo` value on the page), rebuild, check the crop at desktop and phone, adjust `--pos` and `--pos-m`, commit, mark the row Done.
- Where the choices come from: `tools/photos/candidates.py`, run by `tools/build.py`, copies the 800 px file (`sl26-<id>-t.webp`) of every candidate into `photo-candidates/` and writes `photo-candidates/candidates.json`. Each slot draws from one or more of the headings in `manifest.py` (drone, the land, the clubhouse and grounds, members at play); the map is `SLOTS` in `candidates.py`. The photo already in a slot is not offered, top photos skip portrait and near square files, and the banquet room is offered only in the Member's Area.
- Left out on purpose: every junior spot (the home page Junior Golf card, the Junior Golf page) until photo consent is confirmed.
- To add more photos from the PC (the full Rich Nixx library is on the PC drives):
  1. On the PC, add a line for each photo to `tools/photos/manifest.py` under the heading it fits (drone, the land, the clubhouse and grounds, members at play), with alt text that follows the rules below.
  2. With Spring Lakes Media Drive 1 plugged in, run `python tools/photos/export.py`. It writes the three web sizes into `tools/photos/img/`.
  3. Commit `manifest.py` and the new files in `tools/photos/img/`, and push.
  4. On the Mac, pull and run `python3 tools/build.py`. The new photos show up in the picker for every spot that uses their heading.

## Rules that still apply
- The standing heron is the only logo. Nothing showing the old flying heron (pin flags, tee markers, signs, cart roofs, the entrance stone emblem) or the 10 Years badge.
- No junior photos on public pages until consent is confirmed. No food, bar or patio dining photos on public pages.
- At most three Canada flag pins in the gallery.
- Alt text: one plain sentence, no dashes, no staff or member names.
- Never commit the photographer's gallery links.

## Still to come
- Member Guest photos are not downloaded yet.
- Drive 2 (F:) has not been mirrored since the Club Championship set was sorted.
