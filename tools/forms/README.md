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
