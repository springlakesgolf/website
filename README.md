# springlakesgolf.com rebuild

Static site that replaces the Lightspeed WordPress site after the 2026 season.
Page folders match the live URLs so no links break.

- Source design: `~/Downloads/Marketing & Promotions/springlakes-site/` (June 2026)
- Rebuild: `python3 tools/build.py` (copies the June pages into live URL folders, applies brand/content fixes)
- Photos: the 2026 photo set lives in `tools/photos/` and is laid over the June images on every rebuild. See `PHOTO-REFRESH.md`. On the PC (no June source folder): `python tools/photos/photos.py`
- Launch form: one setting, `LAUNCH` at the top of `tools/build.py`. `"soft"` (the default) builds what goes live first: no Shop links, the flying heron, and only the members area pieces switched on in `MEMBER_PIECES` just below it (restaurant reservations are off). To flip to the full launch on the logo release date, change it to `LAUNCH = "full"` and run `python3 tools/build.py`. `SLG_LAUNCH=full python3 tools/build.py` builds the other form once without changing the file. Each members area piece goes live by setting its own line to `True`.
- Tests: `python3 -m unittest tools/test_build.py` builds both forms in temporary folders and checks them (soft: no Shop link, no standing heron file).
- Local preview: `.claude/launch.json` (port 8742 on the Mac, 8743 on the PC)

Preview build: noindex, forms inert, member documents left out.
