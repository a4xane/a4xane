# Validation sprint: Lead Response System (14 days)

**Goal:** find out whether the thesis (`docs/strategy/lead-response-thesis.md`) is worth building, using money received rather than opinions.
**Cash budget:** ≈ ₹0–2,000 (printing, travel, one Razorpay/UPI setup).
**Time budget:** about 2 hours a day around college, plus two half-days of walk-ins.

## Gates (decide in advance, don't move them afterwards)

| Checkpoint | Result | Action |
|---|---|---|
| After the audit (day 6) | ≥ 70% of a vertical replied within 5 min | The problem is absent there. Drop that vertical. |
| After the audit | All three verticals drop | Kill the thesis. Log it in `DECISIONS.md` with the data. |
| After 30 outreach touches | < 5 conversations booked | The message or channel is wrong. Switch to walk-ins and warm intros before changing the offer. |
| After 30 conversations | 0 paid pilots | A value or price problem. Re-read the interview notes, then change one thing. |
| After 30 conversations | **≥ 3 paid pilots** | **GO.** Deliver the pilots (`docs/operations/pilot-spec.md`), then productise. |

A verbal "yes, interested" is not a pilot. **Only money received counts.**

## Day-by-day

| Day | Do | Output |
|---|---|---|
| 1 | Build the list: 60 businesses (20 per vertical) that are actively paying for leads | `tools/response-audit/data/audits.csv` rows (business, vertical, area, phone, source) |
| 2–3 | Send enquiries (protocol below), about 30 a day, Mon–Sat 10:00–18:00 | `channel` and `enquiry_at` filled in |
| 2–6 | Record replies as they arrive; stay quiet for up to 3 days to count follow-ups, then disclose | `human_response_at`, `auto_reply`, `asked_qualifying`, `tried_to_book`, `followups` |
| 6 | The 3-day audit windows have closed. Run `python3 audit.py data/audits.csv --pdf` and check the vertical gates. The numbers only count closed windows, so running earlier just shows fewer rows, not rosier ones. | `summary.md`, reports, outreach |
| 6–10 | Outreach in priority order A → B; C gets the "learn from you" ask | Conversations booked |
| 7–14 | Discovery conversations (script below); propose the pilot the same day when it fits | Notes in `pipeline.csv`; payments |
| 10–12 | Walk-ins with printed reports for A-priority businesses that haven't replied | Conversations |
| 14 | Review against the gates. Write the decision into `DECISIONS.md`. | GO / change one thing / kill |

Log these numbers every day: enquiries sent · replies recorded · outreach sent · conversations booked · conversations held · pilots proposed · **pilots paid**.

## Step 1: Build the list

- **Meta Ad Library** (facebook.com/ads/library): country India, "All ads", status Active. Search the vertical plus the town (e.g. `2BHK Vapi`, `flats Valsad`, `dental clinic Surat`, `NEET coaching Vapi`). Anyone with an active lead ad is paying for leads. Note that a broker's ads appear under the broker's page, not the developer's.
- **Property portals** (99acres, MagicBricks, Housing): agents with active listings in your area.
- **Google Maps / JustDial:** clinics and coaching institutes with many reviews, which suggests volume.
- **Start from the seed list** of 40 businesses (delivered privately; put it in `tools/response-audit/data/audits.csv`). Check each one in the Ad Library for active ads, drop the rows marked `SKIP`, and add more until you have 60.
- **Skip:** businesses with no visible lead spend or volume, and national chains (Aakash, PW and similar). Their leads are handled centrally, so the local branch can't buy.

## Step 2: Audit protocol (ethics are part of the method)

1. **Use your real name and number.** No fake identities.
2. **Never submit a paid lead form.** It costs them ad money. Use WhatsApp, their website form, a phone call or an Instagram DM.
3. **Send only Mon–Sat 10:00–18:00.** Off-hours results are unfair, and the tool flags them.
4. **Ask one realistic, specific question**, the kind a real customer asks:
   - Real estate: *"Hi, I saw your project. Is a 2BHK still available, and what's the price range?"*
   - Clinic: *"Hi, do you do teeth cleaning? What does it cost and when's the next slot?"*
   - Coaching: *"Hi, what are the fees and batch timings for Class 11 science?"*
5. **Record the first reply from a person** (not the auto-greeting), then stay quiet to count follow-ups.
6. **Disclose within 3 days, or sooner if they spend real effort** (a callback or a detailed quote): *"Thanks for the quick reply. To be honest, I'm researching how local businesses handle enquiries and I'm not buying right now. Sorry for taking your time. I'll share what I found if it's useful."* Don't let a salesperson chase a buyer who doesn't exist.
7. **Never share one business's result with anyone else.** Publish anonymised totals only, once N ≥ 30.
8. If anyone asks to be left out, delete their row.

## Step 3: Outreach

Run the tool. `out/outreach/<slug>.md` has WhatsApp, email, walk-in and follow-up copy built from each business's own result. Adapt it into your own voice and language (Gujarati, Hindi or English, whatever they reply in). Rules:
- **One follow-up only** (day 3). After that, a walk-in or nothing.
- **Send the report only after they say yes** to "Can I send it?" A PDF from an unknown number looks like spam.
- **Email:** keep the opt-out line and honour every "no".

## Step 4: Discovery conversation (15–25 min; learn first, pitch last)

Talk about their past and present, not hypotheticals. Avoid "Would you use…?"

1. Walk me through what happens today when a new enquiry comes in. Who sees it first?
2. Where do your leads come from? Roughly how many a month? What do you spend to get them?
3. What happened with the last lead that went cold? How did you find out?
4. How quickly does someone usually reply? After hours? On Sundays?
5. What have you tried to fix this: an app, a CRM, a person, Privyr, a chatbot? **Why did you stop?**
6. How do you know which ad or source actually brings buyers?
7. What is one extra customer (or closed deal) worth to you?
8. If this were solved, what would be different in 3 months?
9. Who else would be involved in deciding to try something?

Write down their numbers: leads per month, value per customer, and current reply time. They go straight into the break-even formula.

**Signals of real pain:** they already spend money or time trying to fix it, give numbers without hesitating, or bring in their salesperson. **Signals of politeness:** "interesting", "send me details", "maybe after Diwali".

## Step 5: Pilot proposal and close

Say it only after discovery shows pain and volume:

> "Here's what I'd do for 30 days. Every new lead gets a WhatsApp reply within a minute, day or night. It asks your qualifying questions and offers visit slots. When someone's serious, your salesperson gets an alert with a summary and takes over. Weekly report: how many leads, how fast, how many booked. Before we start we agree one number, say booked visits per 100 leads compared with last month. Setup and the 30 days cost ₹9,999. If the number doesn't move, you stop and owe nothing more. If it works, it's ₹7,999 a month after that and you can cancel any month. You'd pay WhatsApp's own message charges directly on your account, so the number and the data stay yours. Shall we start Monday?"

Then stop talking. Collect payment by UPI or a Razorpay link **before** setup starts, and send the one-page agreement (scope, metric, price, data-processing clause, cancellation).

## Objections

| They say | You say |
|---|---|
| "My staff already replies." | "Great. Then the pilot will show it, and you'll have proof. Your result from my test was ___." |
| "Leads are junk anyway." | "That's exactly why qualification helps. Your salesperson only gets the ones who answer the questions." |
| "Too expensive." | "What's one extra [deal/patient] worth to you? … So it pays for itself at ___ a month. If it doesn't do that, you stop." |
| "I use Privyr / AiSensy." | "How fast are replies today? Who writes and maintains the flows? I run it for you and I'm measured on the result." |
| "Send me details." | "Sure. What would you need to see in them to say yes to a 30-day pilot?" |
| "After Diwali / next month." | "Understood. Leads coming in now still go cold now. Want to start with one ad campaign only?" |
