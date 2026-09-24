# Thrumline website

**Status: BUILT, NOT DEPLOYED.** There is no live URL yet.

Plain HTML and CSS with a few lines of JavaScript: no framework, no build step, no cookies or trackers. Fonts are self-hosted. The site is about 110 KB before images.

| File | What it is |
|---|---|
| `index.html` | The offer page: hero, the leak, how it works, fit, break-even calculator, pricing, founder, FAQ |
| `privacy.html` | Privacy policy. Meta asks for one for lead ads and WhatsApp business verification. |
| `assets/` | Favicon, link-preview image (`og.png`), fonts (SIL OFL) |
| `robots.txt` | Lets search engines index the site |

## Before it goes live (in this order)

1. **Pick and buy a domain in your own name.** I could not check availability. Try `thrumline.in`, `thrumline.co` and `getthrumline.com`, in that order. Hostinger works, since you already use it.
2. **Make the link preview work:** in `index.html`, change `content="assets/og.png"` to the full address, e.g. `content="https://thrumline.in/assets/og.png"`. WhatsApp and LinkedIn previews need the full URL.
3. **Add an email address** once you have one on the domain (e.g. `kanish@thrumline.in`): put it in the footer of both pages and the contact box in `privacy.html`.
4. **Tap every WhatsApp button on your own phone.** Each one opens a chat with +91 83470 55841 and a pre-filled message.
5. **Set up the WhatsApp Business profile first** (`docs/marketing/launch-plan.md`). Prospects will message you from this page.
6. **Answer fast.** The page sells replies in under 60 seconds and invites people to test you. A slow reply from you kills the pitch.

## Deploy (pick one)

- **Hostinger:** hPanel → Websites → File Manager → `public_html` → upload everything *inside* `site/` (not the folder itself).
- **Netlify:** app.netlify.com/drop → drag the `site/` folder. Then add your domain under Domain settings.
- **Vercel:** import this repo, set the root directory to `site`, framework "Other", and leave the build command empty.

## Editing

- **Price** appears in `index.html` in five places: the break-even intro line, the pricing card (₹9,999 and ₹7,999), and the calculator script (`const FEE = 7999` plus two text lines). Search for `7,999`, `9,999` and `7999`. Also update `brand/BRAND.md` and `docs/strategy/lead-response-thesis.md`.
- **"Taking 3 pilot clients"** is true now. Change it when the pilots are full.
- **Never add** testimonials, client logos or numbers you can't back up (`brand/BRAND.md` → Never). Add real ones, with permission, after the pilots.
- The privacy policy is a plain-language draft, **not legal advice**. Have it reviewed along with the pilot agreement before client 3.
