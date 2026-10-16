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
