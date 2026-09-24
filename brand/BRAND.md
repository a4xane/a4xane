# Thrumline brand guide

**Status:** v1, 2026-09-24. Nothing here has been tested with customers yet. Revise it after the first 10 conversations, using the words owners actually use.

## Decision: one brand, not two

The Lead Response System is sold as **Thrumline**, not under a new name. A second brand would split credibility you haven't built yet, cost a second domain and set of profiles, and confuse local buyers who meet you in person. The offer has a descriptive name ("Lead Response") until a client asks for it by a different one.

**Name check (2026-09-24):** a web search for "Thrumline" found only a knitting pattern and a song, plus a US IT firm spelled "Thruline". There was no business conflict in India. **I could not check the Indian trademark register.** Search it at ipindia.gov.in before you print anything expensive.

## Positioning

> **For** owners of businesses in the Vapi–Valsad–Silvassa–Daman area who pay for leads (real-estate developers and brokers, high-ticket clinics)
> **who** lose enquiries because nobody replies fast or follows up,
> **Thrumline** sets up and runs a WhatsApp system that **answers every lead in under 60 seconds**, asks your qualifying questions and books the visit, so your team only talks to serious buyers.
> **Unlike** WhatsApp tools you have to configure and maintain yourself, **we run it for you and we're measured on booked visits**.

## Messaging

| Layer | Line |
|---|---|
| Tagline | **Never leave a lead on read.** |
| Promise | Every enquiry answered on WhatsApp in under 60 seconds, day or night. |
| Proof we can say today | What the system does, and our local response-time measurements once N ≥ 30. **Nothing else until pilots produce results.** |
| Offer | 30-day pilot, ₹9,999 including setup. Then ₹7,999/month, cancel any month. One agreed number; if it doesn't move, you stop. |
| Ownership | Your number, your data, your WhatsApp account. |
| Founder line | You work directly with Kanish Shah, and he answers his own WhatsApp fast. |

**Three messages, in order of priority:**
1. **The leak.** "You paid for the lead. Then it waited." Speed is the problem owners feel.
2. **The fix.** "Reply in 60 s → your questions → a booked visit → your salesperson takes over."
3. **The risk reversal.** "One number agreed up front. If it doesn't move, you stop."

## Voice

- **Direct, specific, numbers first.** "Replied in 4 h 12 min", not "slow responses".
- **The owner's words, not agency words.** Visits, patients, bookings, enquiries. Not "conversion funnel", "omnichannel" or "synergy".
- **Honest by default.** Say what is measured and what isn't. No "guaranteed sales", no "10x", no "AI revolution".
- **Say "AI" rarely.** Owners buy a booked visit, not a model. Mention AI when explaining how it works or answering "is this a bot?", and say it plainly: *"An assistant trained only on your approved information. When it's unsure, it hands over to your team."*
- **Language:** English on the website. In WhatsApp and in person, use whatever the owner replies in: Gujarati, Hindi or English.

| Say | Don't say |
|---|---|
| "Every lead gets a reply in under 60 seconds." | "Instant AI-powered engagement" |
| "Your salesperson only talks to people who answered your questions." | "Qualified pipeline optimisation" |
| "If the number doesn't move, you stop." | "Guaranteed results" |
| "We tested N businesses; X% replied within 5 minutes." (real data only) | "Most businesses lose 80% of leads" (made-up stat) |

## Visual identity

| Token | Hex | Use |
|---|---|---|
| Ink | `#0E1116` | Primary dark: hero sections, text on light |
| Paper | `#F7F6F2` | Primary light background |
| Lime | `#C7F25A` | Signal accent, **on Ink only** (≈ 14:1 contrast). Never lime text on Paper. |
| Moss | `#3F6212` | Lime's accessible partner on light backgrounds (≈ 6.8:1 on Paper) |
| Ember | `#E4572E` | "Lost lead" moments only: timers, missed replies. Large text or graphics only; for small text use `#B8401C`. |
| Mist | `#E7E5DF` | Lines, borders on Paper |
| Slate | `#5B616B` | Secondary text on Paper |
| Fog | `#9BA1AA` | Secondary text on Ink |

Do **not** use WhatsApp's green (`#25D366`) or read-tick blue as brand colours. We work *on* WhatsApp; we are not WhatsApp.

**Type:** Instrument Sans (400–700) for everything, and Instrument Serif *Italic* for one accent phrase per headline ("on read."). Both are self-hosted in `site/assets/fonts/` under the SIL Open Font License.

**Mark:** a pulse line (the "thrum": always on) ending in a dot (online). It sits on an Ink rounded square (`brand/mark.svg`), or stands alone in Lime on Ink (the profile photo). Keep clear space of at least half the mark's height. Don't recolour the pulse, add gradients or stretch it.

**Wordmark:** "thrumline", all lowercase, Instrument Sans SemiBold, tight tracking (`brand/logo.svg`, `png/logo-*.png`).

## Assets

| File | Size | Use |
|---|---|---|
| `mark.svg`, `logo.svg` | vector | Website, documents |
| `png/profile-800.png` | 800×800 | WhatsApp Business, Google Business Profile, LinkedIn/Instagram avatar |
| `png/og-1200x630.png` | 1200×630 | Link preview image (also used by the website) |
| `png/linkedin-banner-1584x396.png` | 1584×396 | LinkedIn cover (left side left clear for the profile photo) |
| `png/post-01-1080.png` | 1080×1080 | First post / WhatsApp Status |
| `png/logo-dark.png`, `png/logo-light.png` | 1200×360 | Wordmark lockups |

To regenerate after editing `src/assets.html`, run `node brand/src/export.js` (needs Playwright).

## Never

- Fake testimonials, invented client logos, "trusted by 100+ businesses", made-up statistics, or counters that aren't real.
- Naming any business from the response-time audits, or showing screenshots of their chats.
- Stock photos of people in headsets.
