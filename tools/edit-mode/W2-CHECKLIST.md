# W2 go-live checklist

Do these in order. If the workflow reaches `main` before the script and secrets are in place, it fails every 15 minutes.

## 1. Apps Script (Website Edits)
- [ ] Approve the `clasp push` and the deploy to the existing deployment (version 3, the /exec URL stays the same).
- [ ] In the editor, run `setup` once. It adds the **PR** and **Claude note** columns, adds **PR open** and **Needs Cullen** to Status, and creates `BOT_SECRET`. It keeps `EDIT_KEY`.
- [ ] Copy `BOT_SECRET` from the execution log for step 2. Do not paste it into chat or any file.

## 2. GitHub (springlakesgolf/website, Settings)
- [ ] Secrets and variables > Actions > New repository secret `EDITS_BOT_SECRET` = the `BOT_SECRET` value.
- [ ] New repository secret `ANTHROPIC_API_KEY` = a key from the **Club Website** workspace. Making a second key named "Website edits Action" lets you revoke it without breaking W1.
- [ ] Actions > General > Workflow permissions: tick **Allow GitHub Actions to create and approve pull requests**.

## 3. Merge
- [ ] Approve the push of `claude/claude-api-edits-6ebbdd` and the PR, then merge it. The 15-minute schedule only runs from `main`.
- [ ] Actions > Staff edits > Run workflow once. It should log "0 new row(s)" or one line per row.
- [ ] Leave one real test request through Suggest an edit. Within 15 minutes the row should show **PR open** with a link, or **Needs Cullen** with a reason.

## After
- Review each PR's diff, merge it to publish, then set the row to Done.
- Check spend on the Console's Cost page after the first month. W2 is about $0.05 to $0.20 per request.
- When a staff edit is folded into the June source, delete its `tools/edit-mode/staff-edits/<id>.json`. `build.py` stops and names the file if the old text is gone.
