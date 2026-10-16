# Restaurant reservations

Members book from the Dining page. Staff run the day from /dining-staff/ on the restaurant iPad.
The spec and plan are in CullenAI/Knowledge (Restaurant-Reservations-Spec-2026-10-16.md and -Plan-).

- **Sheet:** "Restaurant Bookings" in cullenpacas@gmail.com, private. Its ID and the script link
  live in `config.local.json`, which is gitignored and never committed, because the repo is public.
  `config.json` holds only the public web app address.
  - Laura changes the hours, limits, Staff PIN (6 or more digits) and Email mode in Settings.
  - **Events:** one row per member calendar event, with the dining room set to Open, Closed or Limited (plus a guest limit).
  - **Members:** member number and last name, refreshed from the member list. Never copy it into this repo.
- **Script:** the standalone Apps Script project "Restaurant Bookings". To update it:
  1. Run `python3 tools/dining/build_gs.py`.
  2. Paste `dist/Dining.gs` into the editor and save.
  3. Deploy > Manage deployments > edit > New version. The web address stays the same.
- **Local work:**
  1. Run `node tools/dining/mock_server.js 8745` (PIN 111111, member 1234 / Test).
  2. Build with `SLG_DINING_EXEC=http://localhost:8745/exec python3 tools/build.py`.
  3. Rebuild with a plain `python3 tools/build.py` before committing.
- **Tests:** `node --test tools/dining/*.test.js` covers the rules and runs the Apps Script offline against a fake sheet.
- **Before members use it:**
  - Laura answers her questions.
  - Load the real Members list.
  - Set Email mode to Live.
  - Send confirmations from a club dining address. That means moving the script to that account and redeploying, which changes the web address in config.json.
  - Load the 2027 calendar events.
  - Save /dining-staff/ to the iPad home screen.
  - Review the PIN lockout: one shared counter, so wrong guesses can lock staff out for 15 minutes.
