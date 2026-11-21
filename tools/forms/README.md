# Camp and Lost & Found forms

Design agreed with Cullen on 2026-10-17 for staff edits E6 (camp waitlist, December sign-up) and E8 (lost item reports).

## What gets built
`build_forms.gs` creates three Google Forms in the Drive of whoever runs it, each with its own response Sheet and an email on every submission:

| Form | State | Alerts | Fields |
|---|---|---|---|
| 2027 Camp Waitlist | open | braeden@ | parent name, email, phone; camper name, age next summer (6 to 14), weeks wanted, member family, notes |
| 2027 Camp Registration | closed until December | braeden@ | waitlist fields plus polo size, golf experience, allergies or medical notes, emergency contact, photo permission, $599 fee acknowledgement. Payment: our team contacts each family; no card details in the form |
| Lost Item Report | open | reception@ | name, email, phone, what was lost, description, where, hole or area, date lost |

No items are listed on the members page any more; reception works from the Lost Item Report Sheet.

## Run it once
1. script.google.com, New project, paste `build_forms.gs`, run `buildAll`, approve the permissions.
2. Open View, Logs. Copy the three `live` links into `tools/forms/config.json`:
   ```json
   {"waitlist": "https://docs.google.com/forms/d/e/.../viewform",
    "registration": "https://docs.google.com/forms/d/e/.../viewform",
    "lost": "https://docs.google.com/forms/d/e/.../viewform",
    "registration_open": false}
   ```
3. Share the forms and Sheets with Braeden (camp) and reception (lost items) as editors.
4. `python3 tools/build.py`, check, commit, push.

Running `buildAll` a second time makes a second set, so run it once.

## On the site
- Junior Golf page camp card: "Join the 2027 waitlist" once `waitlist` is set; "Inquire about camp" until then.
- In December: open the Registration form (Responses, Accepting responses), set `"registration_open": true`, rebuild. The button becomes "Register for camp".
- Members page Lost & Found: a short note and a "Report a lost item" button once `lost` is set; the note says to call the pro shop until then.
- Form links open in a new tab. The links are public, so they are fine in this public repo.

# Junior Academy application (/junior-golf/academy/)

Built 2026-11-20 from the Braeden meeting. The form asks for player name, age, years playing, handicap
(if any), tournaments played (if any), and a parent or guardian's name, email and phone. It stays closed
until Cullen opens it in February 2027.

## Files
| File | What it is |
|---|---|
| `academy.gs` | the Apps Script web app. It makes its own Google Sheet, "Junior Academy Applications", apart from the Spring Lakes Website sheet, because the rows are about minors |
| `academy.js` | the page script (copied to `assets/js/academy.js` by the build) |
| `academy.json` | what ships: `{"exec": "", "open": false}` |
| `academy.test.js` | offline test of `academy.gs`: `node --test tools/forms/academy.test.js` |
| `academy_mock.js` | local stand-in for the script, for a browser check |

The sheet has three tabs: **Applications**, **Test** and **Settings**. Settings:

| Setting | Starts as | Meaning |
|---|---|---|
| Accepting applications | No | Yes takes entries; No answers "Applications open in February" |
| Mode | Test | Test writes to the Test tab and sends the alert, marked [TEST], to the test address. Live writes to Applications and alerts the alert address |
| Alert email | braeden@springlakesgolf.com | who hears about each live application |
| Test alert email | cullen@springlakesgolf.com | who hears about each test application |

Every alert has the family's email as reply-to. A repeat of the same request (a retry) adds no second row,
a filled honeypot is dropped, and cells that start like a formula are kept as text.

## Cullen's one-time setup (about five minutes)
1. script.google.com, New project, name it "Junior Academy Applications". Paste `academy.gs` over the sample code. Save.
2. Run `setup`. Click Review permissions, pick the club account, Allow. View, Logs shows the new sheet's link.
3. Deploy, New deployment, type Web app. Execute as: Me. Who has access: Anyone. Deploy, and copy the Web app URL (ends in `/exec`).
4. Put it in `tools/forms/academy.json` as `"exec"`, leave `"open": false`, run `python3 tools/build.py`, commit, push. The page still shows the closed notice.
5. Test it: in the sheet set Accepting applications to Yes (Mode stays Test), build a scratch copy with `SLG_ACADEMY_OPEN=1`, send one application, check the Test tab and the [TEST] email, then set Accepting back to No.
6. In February: Settings, Accepting applications Yes, Mode Live; `academy.json` `"open": true`; rebuild, commit, push. Share the sheet with Braeden.

## Local check (no Google needed)
```
cp -R tools /tmp/academy-check/tools
SLG_ACADEMY_EXEC=http://127.0.0.1:8756/exec SLG_ACADEMY_OPEN=1 python3 /tmp/academy-check/tools/build.py
node tools/forms/academy_mock.js /tmp/academy-check 8756 /tmp/academy-check/rows.json
```
Open http://127.0.0.1:8756/junior-golf/academy/, send an application; it lands in the Test tab of `rows.json` with a [TEST] alert.
