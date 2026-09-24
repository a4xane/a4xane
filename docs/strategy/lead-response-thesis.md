# Lead Response System: business thesis

**Status: EXPLORING.** So far there have been no customer conversations, no pilots and no revenue. Every number below is labelled as a fact (with a source), an assumption, or an illustration.
**Owner:** founder. **Last updated:** 2026-09-24. **Decision record:** `DECISIONS.md` D-002.

## The bet in one sentence

> Local businesses that **pay for leads** (Meta ads, property portals, directory listings) lose a real share of those leads because **nobody replies fast or follows up**. They will pay **₹8–10k a month** for a done-for-you system that replies on WhatsApp within a minute, qualifies the lead, books a visit and hands hot leads to a person.

Only the existence of these businesses is close to certain. Everything else in that sentence is unproven. The 14-day sprint in `docs/sales/validation-sprint.md` is designed to prove or kill the bet with almost no cash spend.

## Why this bet and not the others

| Option | Verdict | Reason |
|---|---|---|
| **Lead Response System** | **Test first** | It is a revenue problem with a measurable before/after (reply time, booked visits). You can deliver it by hand with n8n, WhatsApp and an LLM before any software exists. It sits next to what Thrumline already sells (Meta ads). The test (a response-time audit) also works as the outreach. Because revenue per client is higher, ₹50k MRR needs about 7 clients instead of 28. |
| Websites for local businesses without one | Rejected | Commoditised in India, one-off revenue, and not AI. Thrumline already covers it. |
| AI voice receptionist / calling agent | Later, as an add-on | Higher technical and reliability risk (mixed Gujarati/Hindi/English speech), per-minute costs, and telemarketing rules still to check. Add it once WhatsApp clients ask for it. |
| AI email management | Rejected for this customer | Local Indian SMB leads arrive on WhatsApp and phone, not email. |
| CPA Conversion System (US) | Historical, parked | Trust and channel barriers from India. It is website work, not AI. |
| FLUX, Quote-to-Cash, AI Business Analyst | Historical | Not reactivated (master context §42). |

---

## 1. Market

- **Fact:** Meta's Ad Library shows any page's active ads and can be searched by keyword and country ([mida.so guide](https://www.mida.so/blog/meta-ads-library), [adlibrary.com](https://adlibrary.com/posts/real-estate-agency-ads)). You can therefore list the businesses that are paying for leads right now, which is the best available proof of lead spend.
- **Assumption:** there are enough such advertisers in South Gujarat (real estate, clinics, coaching) to fill a pipeline.
- **To validate on sprint day 1:** find at least 60 active local advertisers in one working day. If you can't, the local market is too thin: keep the offer and expand to Surat, Mumbai or Pune remotely.

## 2. Customer (ICP hypothesis)

| | Primary | Secondary |
|---|---|---|
| Who | Real-estate developers and channel partners with active lead ads or portal subscriptions | Private clinics (dental, dermatology, physio, IVF) and coaching institutes |
| Why them | One extra deal is worth a lot. Lead volume is high and lead quality poor, so qualification has value. The owner decides. | They take appointments, run frequent ads, and the owner decides |
| Decision maker / budget | Owner or partner | Owner or doctor |
| Disqualify if | Fewer than about 50 leads a month (assumption), nobody to hand leads to, or unwilling to share lead data | Same |

Don't assume the winner. The audit covers all three verticals, and the data picks one.

## 3. Problem

**Hypothesis:** leads get a reply late or not at all, follow-up is inconsistent, and the owner can't see what happens to a lead.

**Evidence so far (thin):** there is one study, and it is old and American. An HBR audit of 2,241 US companies found that 37% responded to a web lead within an hour, 24% took more than 24 hours and 23% never responded. The average response time was 42 hours. Firms that tried to contact a lead within an hour were nearly 7× as likely to qualify it as those that waited even an hour longer, and more than 60× as likely as those that waited 24 hours or more ([HBR, March 2011](https://hbr.org/2011/03/the-short-life-of-online-sales-leads); figures via [Vivocha summary](https://www.vivocha.com/short-life-online-sales-leads/)). **There is no local data.** The audit creates it.

## 4. Current workarounds and competitors

| Workaround | What it does | Price (source) |
|---|---|---|
| Owner, receptionist or salesperson replying from their phone | Replies when free | Staff time |
| WhatsApp Business app auto-greeting | Instant "thanks, we'll get back to you" | Free |
| **Privyr** | Pushes Facebook leads to your phone in real time for instant WhatsApp/SMS follow-up. Marketed at Indian real-estate agents. | Free plan; paid plans reported from $15, Pro $35/month ([Techjockey](https://www.techjockey.com/detail/privyr)); unverified on Privyr's own page |
| WhatsApp BSP chatbots (AiSensy, Interakt, WATI) | Do-it-yourself flows and broadcasts on the WhatsApp API | AiSensy ₹1,500–3,200/month; Interakt from ₹2,499/month ([AiSensy](https://aisensy.com/pricing), [comparison](https://www.go4whatsup.com/blog/aisensy-vs-wati-vs-interakt-pricing-showdown-2026/)) |
| CRMs (LeadSquared, TeleCRM, Kylas and others) | Lead management | Not researched yet |

**Brutal point:** the software already exists and is cheap. If owners using Privyr or AiSensy reply fast and are happy, the wedge is gone. The only defensible offer at this stage is **"we run it for you and are measured on the outcome"**, not "we built better software". Interviews must ask: *What have you tried? Why did you stop?*

## 5. Why it matters (in the customer's own numbers)

Never quote a generic loss figure. Fill this in with the customer during discovery:

```
Monthly revenue at risk = leads/month × share not answered within 5 min
                          × extra conversion if answered fast × value per customer
```

The honest pitch is the **break-even** figure, which needs no forecast:

```
Extra customers needed per month to pay for the service = monthly fee ÷ value of one customer to them
```

*Illustration only, not data:* if one closed deal is worth ₹50,000 to a broker, then ₹7,999 ÷ ₹50,000 = 0.16 deals a month, or about one extra deal every 6 months. If a new clinic patient is worth ₹3,000, then ₹7,999 ÷ ₹3,000 = 2.7 extra patients a month. The customer supplies the real values.

## 6. Solution (pilot scope)

1. Every new lead (Meta lead form, click-to-WhatsApp ad, website form) gets a WhatsApp reply in under 60 seconds, 24×7.
2. An AI assistant **limited to that business** answers only from approved facts, asks the client's qualifying questions and offers visit or appointment slots.
3. Hot lead → the salesperson gets a WhatsApp alert with a summary, and a person takes over.
4. Leads who don't reply get follow-ups on day 1, 3 and 7 using approved templates.
5. A weekly report covers leads, first-reply time, qualified leads, bookings, handoffs, and how fast the salesperson took over.

Not in the pilot: voice calls, CRM integrations beyond Google Sheets, and anything the client hasn't approved in writing. Full spec: `docs/operations/pilot-spec.md`.

## 7. Offer (hypothesis, price to be tested)

- **30-day paid pilot: ₹9,999**, setup included.
- **Then ₹7,999/month**, cancel any month.
- The client pays Meta's WhatsApp charges directly on **their own** WhatsApp Business account. They own the number and the data.
- A success metric is agreed in writing **before** the start. Examples: median first reply under 2 minutes; booked visits per 100 leads compared with their previous month.
- If the metric doesn't improve, they don't continue and owe nothing more. **No revenue guarantees, ever.**

**Price-test rule:** if 4 of the first 5 prospects accept without pushback, the price is too low, so raise it for the next 5 (₹14,999 pilot, ₹11,999/month). If they like the offer but nobody accepts ₹9,999, offer ₹4,999 **once** to find out whether the objection is price or value.

## 8. Validation gate

**GO:** at least 3 paid pilots (money received, not verbal yes) from at most 30 discovery conversations within about 21 days. The other gates are in `docs/sales/validation-sprint.md`.

## 9. Acquisition

1. **Audit-led outreach (primary).** Each business gets its own measured result. Cost: time.
2. **Thrumline's existing network.** Anyone already running ads.
3. **Content, later.** Publish anonymised totals ("I tested N local businesses…") only once N ≥ 30, and never name a business.
4. **Partners, later.** Meta-ads freelancers and agencies generate leads but don't handle them, which makes them natural resellers.

Measure CAC as **founder hours per paying client** until there is paid acquisition.

## 10. Sales process

Audit → first touch with their result → 15-minute walkthrough → discovery with their numbers → pilot proposal the same day → payment by UPI or Razorpay link → kickoff within 48 hours.

## 11–12. Delivery and customer success

See `docs/operations/pilot-spec.md`. The weekly report is the retention tool: value has to be visible every week.

## 13. Retention risks

- **The humans stay slow.** The system replies in seconds, but the salesperson ignores alerts, so booked visits don't rise. Mitigation: measure salesperson take-over time and show it to the owner.
- **Seasonality**, for example coaching admissions. Price and plan per season, or don't target them.
- **The novelty wears off.** The monthly review must show a number that matters to them.

## 14. Operations (pilot stage)

The CRM is a Google Sheet built from `pipeline.csv`. Workflows run on self-hosted n8n. Payments go through UPI or a Razorpay payment link. There is a written agreement that includes a data-processing clause. Log every decision in `DECISIONS.md`.

## 15. Economics

Every row shows its source, the assumption, the formula and the result.

| Item | Source / assumption | Formula | Result |
|---|---|---|---|
| Price | Assumption, untested | | ₹7,999/month |
| Clients for ₹50k MRR | Master context target | 50,000 ÷ 7,999 | 6.25 → **7 clients** |
| Old FLUX-style model, for comparison | Master context §13 | 50,000 ÷ 1,847 | ~28 customers |
| n8n hosting | Assumption: ₹500–1,000/month VPS shared across clients | ÷ number of clients | ₹150–1,000 per client |
| LLM usage | **Unverified estimate** for about 300 leads/month; measure in the pilot | | ₹300–1,000 per client |
| BSP subscription | ₹0 on the direct Cloud API; ₹1,500–3,200 on AiSensy ([source](https://aisensy.com/pricing)) | | ₹0–3,200 per client |
| **Cost to serve (excluding founder time)** | Sum of the three rows above | | **₹450–5,200 per client** |
| **Gross margin** | | (7,999 − cost) ÷ 7,999 | **35%–94%** |
| Meta message fees (the client pays) | India marketing template ₹0.8631, utility ₹0.115, reported for Oct 2026 ([WatEase](https://watease.com/blog/whatsapp-business-platform-pricing-india), [Sendiee](https://www.sendiee.com/blog/whatsapp-pricing-changes-october-2026)). Click-to-WhatsApp ads open a 72-hour free window ([Go4whatsup](https://www.go4whatsup.com/guides/click-to-whatsapp-ads/)). | e.g. 300 leads × 3 marketing templates × ₹0.8631 | ~₹777/month *illustration* |
| Founder time | Assumption: 8–12 h setup, then 3–5 h/month per client; measure it | 7 clients × 3–5 h | 21–35 h/month ongoing |

What the table says:
1. **Fewer, higher-value customers is the right shape for a founder who is studying full-time.** Seven sales conversations that close are more realistic than 28.
2. **A paid BSP per client can wipe out the margin.** Use the direct Cloud API after pilot 1 (D-004).
3. **Founder hours are the real cost.** If setup doesn't drop below about 4 hours by client 4, it isn't productised yet.

## 16–17. Technology and automation

Rule: **no custom software before the first paid pilot. No dashboard or SaaS before 3 clients have renewed at least once.** Already automated: turning audits into reports, outreach and the pipeline (`tools/response-audit`). Automate next, only once it has been done by hand twice: onboarding checklist → weekly report → templated setup per vertical.

## 18. Scale path

| Stage | Clients | Change |
|---|---|---|
| Service | 1–3 | You set up each client by hand from the pilot spec |
| Productised | 4–10 | One template per vertical, 1-day onboarding, fixed pricing. First hire: a part-time ops/QA person who reviews AI conversations |
| Software | 10+ | Multi-tenant workflow and a client dashboard (response time, funnel), built from what the pilots proved |
| SaaS | Only if clients ask to self-manage | Self-serve |

---

## Risk register

| Risk | What would show it | Mitigation |
|---|---|---|
| Market: businesses already reply fast | The audit shows ≥ 70% of a vertical replying within 5 min | Drop that vertical. If it holds for all three, drop the thesis. |
| Customer: can't reach owners | < 5 conversations from 30 touches | Switch to walk-ins and warm intros from the Thrumline network |
| Pricing: value below ₹8k | "Interesting" but nobody pays | Run the price-test rule and read the interview notes before changing the offer |
| Competition: Privyr or AiSensy is enough | Interviewees already use them and are satisfied | Position as "done for you, measured on outcome", or pick a vertical where they aren't used |
| **Platform (Meta)** | Policy or pricing change | Since 15 Jan 2026 Meta **bans general-purpose AI chatbots** on the WhatsApp Business API. Bots for a business's own tasks (support, bookings, sales) remain allowed ([TechCrunch](https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform), [respond.io](https://respond.io/blog/whatsapp-general-purpose-chatbots-ban)). Keep the bot strictly scoped to the client's business. Pricing changes often: free service replies become chargeable after 1,000/month from 1 Oct 2026 (reported by BSPs). |
| Opt-in | Messages sent without consent → number quality drops or gets banned | Lead forms carry WhatsApp consent text. Honour opt-outs (STOP) immediately. *Check the exact wording in Meta's current messaging policy; I have not read the primary page.* |
| **Data / privacy (DPDP)** | Client's customer data mishandled | DPDP Rules were notified 13 Nov 2025. Most obligations (notices, security safeguards, breach notification) apply from 14 May 2027 ([PIB notification](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf), [timeline summary](https://dpdpa.dcomply.in/rules/)). You act as a **Data Processor** for the client, so have a written contract, minimal data, deletion when the contract ends, and client-owned accounts. Build this now instead of retrofitting it. *Not legal advice; get a lawyer to review the agreement before client 3.* |
| Reliability: the AI says something wrong | Wrong price or availability quoted | Answers come only from approved facts, the bot hands off when unsure, no discounts or commitments, and a sample of transcripts is reviewed weekly |
| Founder: college load, single point of failure | Missed SLAs | Written SOPs, templated setup, and never promising a human reply time you can't keep |
| Financial | Needs cash before revenue | Sprint cash cost is ≈ ₹0–2,000. Nothing is bought before a pilot is paid. |

## Known / assumed / to validate / test first

- **Known (sourced):** the HBR 2011 response-time findings (US, old). The WhatsApp AI-chatbot policy and the direction of per-message pricing. The DPDP timeline. Cheap tools already exist (Privyr, AiSensy, Interakt).
- **Assumed:** local businesses reply slowly. Owners will pay ₹8–10k a month. AI qualification works in Hinglish/Gujarati text. Salespeople act on alerts.
- **To validate:** whether the problem exists (audit), willingness to pay (paid pilot), whether delivery works (pilot metrics), retention (month-2 renewal).
- **Test first, this week:** audit 60 businesses. Everything else waits for that data.
