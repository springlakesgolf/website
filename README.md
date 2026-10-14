# springlakesgolf.com rebuild

Static site that replaces the Lightspeed WordPress site after the 2026 season.
Page folders match the live URLs so no links break.

- Source design: `~/Downloads/Marketing & Promotions/springlakes-site/` (June 2026)
- Rebuild: `python3 tools/build.py` (copies the June pages into live URL folders, applies brand/content fixes)
- Local preview: `.claude/launch.json` (port 8742)

Preview build: noindex, forms inert, member documents left out.
