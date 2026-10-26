# Suggest an edit

Staff open the preview with `?edit=<key>`, tap **Suggest an edit**, tap the part of
the page to change, and type the change. Each request becomes a row in the
"Website Edits" Google Sheet (owner cullenpacas@gmail.com); photos go to the Drive
folder "Website Edit Photos". URLs are in `config.json`; the key is in
`edit-key.txt` (gitignored, the repo is public) and in the script's properties.

- `edit-mode.js`: the button and picker. `tools/build.py` copies it into
  `assets/js/` with the web app URL filled in, on preview builds only.
- `Code.gs`: standalone Apps Script "Website Edits", web app, execute as me,
  access Anyone; rejects requests without the key. To change it: paste into the
  editor, save, Deploy > Manage deployments > edit > New version (URL stays).
- New key: delete the `EDIT_KEY` script property, run `setup`, send the new link.
  `?edit=off` turns the button off in a browser.
- Test without touching the sheet: `SLG_EDIT_EXEC=http://localhost:8744/exec python3 tools/build.py`,
  run `mock_server.py` (launch config `edit-mock`), open `http://localhost:8744/?edit=testkey`.
  Rebuild with plain `python3 tools/build.py` before pushing.

## Hours and Lost & Found

The same script answers `GET ?feed=content` from the "Website Content" sheet
(`content_sheet` in `config.json`): tab **Hours** (Show to: Everyone, Members only
or Hidden) and tab **Lost & Found** (items stay up until Status is Claimed or 90
days pass). `tools/members/content.js` shows them on the contact page (Everyone
rows only) and the members page. The script caches for a minute.

## Edits done by Claude (W2)

`.github/workflows/staff-edits.yml` runs `staff_edits.py` every 15 minutes (or Actions > Staff edits >
Run workflow). For each row with Status **New** and no PR it asks Claude Sonnet 5.5 for a text-only
change to that one page, opens a pull request on branch `staff-edit/<id>-<page>`, and writes the link
to the **PR** column with Status **PR open**. Anything it is unsure about, or that breaks a rule,
gets Status **Needs Cullen** and the reason in **Claude note**. Nothing goes live until someone
merges the PR; after merging, set the row to Done.

- Rules in code, whatever the model says: only the ten public page files; tags, links and attributes
  unchanged; nothing inside scripts, styles, forms, buttons or the page head (the title is allowed);
  no em or en dashes, "enquiry", emojis, new dollar amounts, new staff names, emails or phone numbers,
  public dining invitations, or pricing words on the membership page; photos always go to Cullen.
- One open PR per page at a time (pages are one line, so two would conflict). Later rows for that
  page wait until it is merged or closed. At most five rows per run.
- Each merged edit also lives in `staff-edits/<id>.json`; `tools/build.py` replays it so a rebuild
  keeps it, and stops if the old text is gone (fold the change into the June source, then delete the file).
- The sheet route is `doPost` with `bot` = Script Property `BOT_SECRET` (repo secret `EDITS_BOT_SECRET`).
  Action logs are public, so they print row ids and statuses only.
- Tests, no key needed: `python3 -m unittest tools/edit-mode/test_staff_edits.py` (Python 3.10+ with
  `anthropic` installed) and `node --test tools/edit-mode/code.test.js`.
- Try Claude on the fixture rows without git, PRs or the sheet:
  `python3 tools/edit-mode/staff_edits.py --dry-run --rows tools/edit-mode/fixtures/rows.json`
  (needs `ANTHROPIC_API_KEY`), or in GitHub: Actions > Staff edits > Run workflow with
  **Test run on the sample rows only** ticked.
