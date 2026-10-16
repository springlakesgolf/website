# Launch checklist

Things that are correct on the staff preview but must change when the site goes live.
From the review on 2026-10-16 (CullenAI/Knowledge/Website-Review-2026-10-16.md, items 6 and 7).

## Before DNS moves
- [ ] Put /members/ behind the shared password, checked on the server (Cloudflare Worker), and test it on a phone.
- [ ] Add the member documents to /members/: the 2027 forms, the calendar, the restaurant menu and the wine list.
- [ ] Wire the forms. Memberships goes to the existing Apps Script inquiry endpoint (Membership Inquiries sheet). Events, dining, contact and renewal go to the same script with a `form` field. Add a hidden honeypot field to each, then send one test submission per form and check it lands.

## In the build
- [ ] Remove PREVIEW_HEAD's `noindex,nofollow` meta and the "Staff preview" pill.
- [ ] Replace `robots.txt` (`Disallow: /`) with an allow plus a sitemap line, served from the domain root.
- [ ] Stop injecting `edit-mode.js`, or keep it behind a separate staff-only preview build.
- [ ] Remove the "Preview only" note on /members/ and the form stub in `site.js`.

## Cutover
- [ ] Change only the `@` A records and the `www` CNAME. Leave MX, `mail`, `autodiscover` and the TXT records alone.
- [ ] Keep the Lightspeed site up for about two weeks, then give notice (calendar reminder set for Dec 1, 2026).
