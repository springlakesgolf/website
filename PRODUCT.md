# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: prospective members, mostly from Stouffville, Markham, Richmond Hill and the north GTA, deciding whether a private club is worth an inquiry. They arrive from search or a referral, look at the courses and the setting, and either inquire or leave.
Secondary, behind the member password: current members booking tee times (Chronogolf), checking hours, weather and club emails, signing up for leagues (Golf Genius), and renewing.
Also: couples and companies looking at weddings and golf days, and parents looking at junior camps and the academy.

## Product Purpose
The club's own website, replacing the Lightspeed-hosted WordPress site after the 2026 season. It has to make a private club worth inquiring about, and it has to give members the few things they use every week without a phone call.

## Positioning
Canada's largest 54-hole private club: three distinct 18-hole courses (North, East, South) on about 400 acres of the Oak Ridges Moraine, with 45 lakes and no clubhouse minimums. Private and inquiry-first.

## Operating Context
- Membership is handled by inquiry. The membership inquiry form posts to an Apps Script that writes to the "Membership Inquiries" sheet.
- Tee times run on Lightspeed Golf / Chronogolf (club 18694), and leagues and events run on Golf Genius.
- Staff suggest site edits through the "Suggest an edit" mode on the preview, which posts to the Website Edits sheet. Hours and Lost & Found come from the "Website Content" sheet.
- Hosting is moving to Cloudflare. The members area will sit behind a shared password checked on the server.

## Capabilities and Constraints
- Static HTML/CSS/JS, built by `tools/build.py`. Live URL slugs must be kept: /, /golf/, /golf-academy/, /golf-camps/, /memberships/, /members/, /events-spring-lakes/, /food-beverage/, /course-gallery/, /contact-us/.
- Never publish membership prices, tiers or feature lists. Every membership path leads to an inquiry.
- Dining is for members and their guests. Do not advertise the restaurant to the public; non-members need a social membership. There is no front BBQ; the back patio remains.
- Public copy says "our team", not staff names.
- No em or en dashes anywhere members or the public read them. Spell it "inquiry".
- No emojis on club graphics.

## Brand Commitments
- Colours: Navy #323C60 (primary), Gold #B89A2D (accent), white. Text on gold is navy, never white.
- Mark: the navy flying heron. The stacked SPRING LAKES / GOLF CLUB / heron lockup is the norm. The 10 Years badge is retired.
- The club name is set in engraved caps (Cinzel), never in a cursive or script font. Headlines are Cormorant and body text is Montserrat.
- Character (Cullen, 2026-10-16): established and quiet. Old-club confidence, restrained and editorial; the land does the talking.
- Direction (Cullen, 2026-10-16): the classic private club look. He likes the current site; refine it rather than replace it. Keep the Golf dropdown; restyle buttons and dropdowns only from options he picks. No text fading in on scroll (a quiet entrance on photos is fine).

## Evidence on Hand
- Current site imagery in `assets/img/` (drone and course shots, clubhouse, gallery).
- A professional photo library from Ritch is coming on hard drives (ordered 2026-10-16). Cullen wants the visual redesign held until it is backed up and sorted.
- The latest club Mailchimp campaigns and a 7-day ECCC forecast on the members page.
- No testimonials, press, awards or member counts are on hand. Do not invent any.

## Product Principles
1. Inquiry over information. Show enough of the club to earn an inquiry, never the price list.
2. The land is the hero. Three courses on the moraine are the claim no neighbour can copy.
3. Members' weekly jobs take one tap: book, hours, weather, leagues, renew.
4. Staff can change what changes often (hours, lost items, edits) without a developer.

## Accessibility & Inclusion
Many members are older. Use readable text sizes and strong contrast, keep tap targets large, and make booking and hours easy to find on a phone.
