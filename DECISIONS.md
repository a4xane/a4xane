# Decision log

The founder decides; Claude proposes. Status is PROPOSED until the founder accepts it.

---

### D-001: Keep private context out of this public repo

- **DATE:** 2026-09-24
- **DECISION:** Don't commit the founder's master context or any client/lead data to `a4xane/a4xane`. Leave the root `README.md` (the GitHub profile page) untouched. Real data goes in gitignored folders.
- **WHY:** The repo is public (checked via the GitHub API on 2026-09-24). The master context includes personal and education details, and audit logs contain third-party business data.
- **ALTERNATIVES:** Commit everything (rejected: publishes personal and third-party data). Make this repo private (hides the profile README). Create a private business repo (preferred; needs the founder's go-ahead).
- **EVIDENCE:** Repository visibility is `public`.
- **CONSEQUENCES:** Future sessions need the context supplied again or read from a private repo.
- **STATUS:** ACCEPTED as a safety default. The founder can override.

### D-002: The Lead Response System is the thesis to validate, not a decision to build

- **DATE:** 2026-09-24
- **DECISION:** Test one bet first: done-for-you WhatsApp speed-to-lead (reply in under 60 s, qualify, book, hand off, follow up) for local businesses that pay for leads. Real estate is the primary ICP; clinics and coaching are secondary. Sold under Thrumline.
- **WHY:** It is a revenue problem with a measurable before/after. It can be delivered by hand first. It is next to Thrumline's Meta-ads work. It can be tested with near-zero cash through an audit that doubles as outreach. ₹50k MRR at ~₹8k ARPU needs about 7 clients, compared with about 28 at ₹1,847.
- **ALTERNATIVES:** Websites for businesses without one (commoditised, not AI). AI voice agent (higher risk; later add-on). AI email management (wrong channel for this ICP). US CPA system and FLUX (historical).
- **EVIDENCE:** HBR 2011 response-time study (US, old). Competitor tools exist at low prices, which proves demand for tooling but also means the wedge must be service and outcome. **No local evidence yet.**
- **CONSEQUENCES:** 14-day sprint. The gates are in `docs/sales/validation-sprint.md`.
- **STATUS:** PROPOSED.

### D-003: Build gates

- **DATE:** 2026-09-24
- **DECISION:** No delivery software until the first pilot payment. No dashboard, multi-tenant system or SaaS until 3 clients have renewed at least once. The only code allowed before that is the sales tooling (`tools/response-audit`).
- **WHY:** The master context requires validation before engineering. The main risk is building something nobody pays for.
- **ALTERNATIVES:** Build a demo bot first (rejected: it's cheap to build in 1–2 days once a pilot is paid, and a demo doesn't prove willingness to pay).
- **EVIDENCE:** None needed. This is a process rule.
- **CONSEQUENCES:** The first pilot needs a 3-day build window after payment (`docs/operations/pilot-spec.md`).
- **STATUS:** PROPOSED.

### D-004: The client owns the WhatsApp account; Meta fees are passed through

- **DATE:** 2026-09-24
- **DECISION:** Each client uses their own WhatsApp Business account and number and pays Meta's message fees directly. Thrumline charges a flat service fee and uses the direct Cloud API rather than a per-client BSP subscription after pilot 1.
- **WHY:** A paid BSP per client (₹1,500–3,200/month) can push gross margin from ~94% to ~35% at a ₹7,999 price. Client ownership also builds trust and simplifies the DPDP processor role.
- **ALTERNATIVES:** Resell messaging with a markup (more revenue, but more billing work and liability). Use a BSP for speed on pilot 1 (acceptable as a one-off).
- **EVIDENCE:** Pricing figures in `docs/research/sources.md` (BSP-reported, not yet verified against Meta's page).
- **CONSEQUENCES:** Onboarding must include setting up the client's WhatsApp Business account and migrating their number.
- **STATUS:** PROPOSED.
