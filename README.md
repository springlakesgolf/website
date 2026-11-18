# springlakesgolf.com rebuild

Static site that replaces the Lightspeed WordPress site after the 2026 season.
Page folders match the live URLs so no links break.

- Source design: `~/Downloads/Marketing & Promotions/springlakes-site/` (June 2026)
- Rebuild: `python3 tools/build.py` (copies the June pages into live URL folders, applies brand/content fixes)
- Photos: the 2026 photo set lives in `tools/photos/` and is laid over the June images on every rebuild. See `PHOTO-REFRESH.md`. On the PC (no June source folder): `python tools/photos/photos.py`
- Local preview: `.claude/launch.json` (port 8742 on the Mac, 8743 on the PC)

Preview build: noindex, forms inert, member documents left out.
