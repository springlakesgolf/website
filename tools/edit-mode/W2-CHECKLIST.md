# W2 go-live checklist

Do these in order. If the workflow reaches `main` before the script and secrets are in place, it fails every 15 minutes.

## 1. Apps Script (Website Edits)
- [ ] Approve the `clasp push` and the deploy to the existing deployment (version 3, the /exec URL stays the same).
- [ ] In the editor, run `setup` once. It adds the **PR** and **Claude note** columns, adds **PR open** and **Needs Cullen** to Status, and creates `BOT_SECRET`. It keeps `EDIT_KEY`.
- [ ] Copy `BOT_SECRET` from the execution log for step 2. Do not paste it into chat or any file.

## 2. GitHub (springlakesgolf/website, Settings)
- [ ] Secrets and variables > Actions > New repository secret `EDITS_BOT_SECRET` = the `BOT_SECRET` value.
- [ ] New repository secret `ANTHROPIC_API_KEY`. Make a new key in the Console (Club Website workspace > API keys > Create key, name it "Website edits Action") and paste it straight into this secret. It is shown only once, so there is nothing to store anywhere else, and revoking it later does not touch W1.
- [ ] Actions > General > Workflow permissions: tick **Allow GitHub Actions to create and approve pull requests**.

## 3. Merge
- [ ] Approve the push of `claude/claude-api-edits-6ebbdd` and the PR, then merge it. The 15-minute schedule only runs from `main`.
- [ ] Live Claude test: Actions > Staff edits > Run workflow, tick **Test run on the sample rows only**. Expect E901 "would open a PR" with a diff, E902 to E907 "Needs Cullen". No PRs, no sheet changes.
- [ ] The sheet has one row already at Status **New** (row 12). The first scheduled run turns it into a PR or a Needs Cullen note; set it to Done first if it was already handled by hand.
- [ ] Leave one real test request through Suggest an edit. Within 15 minutes the row should show **PR open** with a link, or **Needs Cullen** with a reason.

## After
- Review each PR's diff, merge it to publish, then set the row to Done.
- Check spend on the Console's Cost page after the first month. W2 is about $0.05 to $0.20 per request.
- When a staff edit is folded into the June source, delete its `tools/edit-mode/staff-edits/<id>.json`. `build.py` stops and names the file if the old text is gone.
