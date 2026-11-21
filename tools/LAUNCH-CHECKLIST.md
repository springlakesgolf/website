# Launch checklist

Things that are correct on the staff preview but must change when the site goes live.
From the review on 2026-10-16 (CullenAI/Knowledge/Website-Review-2026-10-16.md, items 6 and 7).

## Before DNS moves
- [ ] Put /members/ behind the shared password, checked on the server (Cloudflare Worker), and test it on a phone.
- [ ] Add the member documents to /members/: the 2027 forms, the calendar, the restaurant menu and the wine list.
- [ ] Wire the forms. Memberships goes to the existing Apps Script inquiry endpoint (Membership Inquiries sheet). Events, dining, contact and renewal go to the same script with a `form` field. Add a hidden honeypot field to each, then send one test submission per form and check it lands.

- [ ] Reservations: Laura's answers in Settings, the real Members list loaded, Email mode Live, confirmations from the club dining address, 2027 calendar events loaded, the PIN lockout reviewed, and /dining-staff/ saved to the restaurant iPad home screen. See tools/dining/README.md.

## In the build
- [ ] Soft launch goes live with `LAUNCH = "soft"` in `tools/build.py`. Before DNS moves, check each line in `MEMBER_PIECES` (reservations stay `False` until Laura's settings are real).
- [ ] Full launch, on the logo release date: set `LAUNCH = "full"`, rebuild, check the Shop link and the standing heron, then push.
- [ ] Remove PREVIEW_HEAD's `noindex,nofollow` meta and the "Staff preview" pill.
- [ ] Replace `robots.txt` (`Disallow: /`) with an allow plus a sitemap line, served from the domain root.
- [ ] Stop injecting `edit-mode.js`, or keep it behind a separate staff-only preview build.
- [ ] Remove the "Preview only" note on /members/ and the form stub in `site.js`.
- [ ] Shop link: once Braeden opens the Shopify store (its storefront password page is off) and `shop.springlakesgolf.com` points at Shopify, change `SHOP_URL` in `tools/build.py` to `https://shop.springlakesgolf.com/` and rebuild.

## Cutover
- [ ] Change only the `@` A records and the `www` CNAME. Leave MX, `mail`, `autodiscover` and the TXT records alone.
- [ ] Keep the Lightspeed site up for about two weeks, then give notice (calendar reminder set for Dec 1, 2026).
