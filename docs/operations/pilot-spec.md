# Pilot delivery spec: Lead Response System

**Status: SPEC ONLY. Nothing here is built.** Build trigger: the first pilot payment is received (`DECISIONS.md` D-003). Target: live within 3 working days of payment.

## Architecture (pilot, single client)

```text
 Meta lead form ─┐
 Click-to-WA ad ─┼─► n8n (self-hosted) ──► WhatsApp Cloud API ◄──► Lead
 Website form ───┘        │   ▲             (client's own number)
                          │   │
                          ▼   │
                  AI step (LLM, scoped to this business)
                  in: approved facts + qualifying questions + conversation so far
                  out: JSON { reply, stage, fields, handoff, reason }
                          │
          ┌───────────────┼──────────────────────┐
          ▼               ▼                      ▼
   Google Sheet     Salesperson alert        Follow-up scheduler
   (lead log/CRM)   (WhatsApp template)      (day 1 / 3 / 7 templates)
                          │
                          ▼
                 Weekly report to owner
```

| Component | Choice | Why | Verify before building |
|---|---|---|---|
| Orchestration | n8n, self-hosted on a small VPS | You already know it; costs are fixed per server, not per client | Whether n8n's Facebook Lead Ads trigger node fits the client's setup |
| Messaging | WhatsApp Cloud API on the **client's** WhatsApp Business account | The client owns the number and data; Meta bills them directly; no BSP margin | Number migration: a number already on the WhatsApp Business app needs migration or a new number. Check Meta's current coexistence rules. |
| AI | A small, cheap LLM (e.g. a Claude Haiku-class model) with a strict JSON output | Cost, speed, predictable output | Current model pricing; tested quality in Hinglish/Gujarati text |
| CRM | Google Sheet per client | Zero setup; the owner can see it | Move to their CRM only if they already have one |
| Payments | UPI / Razorpay payment link | Standard in India | |

## Flows

1. **New lead:** webhook or trigger → dedupe by phone → log a row → send the first WhatsApp template within 60 s (a lead form counts as business-initiated, so it must be a pre-approved template) → start the conversation state.
2. **Conversation:** each inbound message → AI step → validate the JSON → send the reply → update the row. Ask the client's qualifying questions one at a time.
3. **Handoff:** a hot lead, a question the approved facts can't answer, a complaint, or anyone asking for a person → alert the salesperson with a summary and a link to the chat → the bot stops replying on that thread until released.
4. **Follow-up:** no reply → day 1, 3 and 7 templates → then mark as cold. Never more than that.
5. **Opt-out:** "STOP", "no", "don't message" (any language) → suppress immediately, confirm once, log it.
6. **Weekly report:** Monday 9:00 to the owner. Content below.

## AI guardrails (non-negotiable)

- Answers come **only** from the client's approved-facts sheet: projects, prices, locations, timings, FAQs. If a fact is missing, the bot replies *"Let me get [name] to confirm that"* and hands off.
- The bot never offers discounts, never commits to availability or dates beyond the approved slot list, and never discusses competitors.
- It is scoped to this business only (Meta's 2026 policy bans general-purpose chatbots). Off-topic requests get a polite decline.
- Structured output is validated before sending. On invalid output, send a safe fallback plus a handoff, and never raw model text.
- All messages are logged. **Review 20 random conversations per client every week** and record the error rate.
- The client approves the facts sheet, templates and qualifying questions **in writing** before go-live.

## Data and compliance

- The client is the data fiduciary and you are the **processor** (DPDP Act). Keep a written agreement with scope, purpose, security measures, breach notice to the client, and deletion within 30 days of the end of the contract.
- Collect only what's needed: name, phone, the answers to the qualifying questions and the conversation. No ID documents, no payment details.
- Lead forms include WhatsApp consent text. Opt-outs are honoured instantly.
- Credentials live in n8n's credential store or environment variables, **never** in this public repo.
- Each client gets a separate sheet and separate credentials, and no data is shared across clients.

## Onboarding (day 0–3)

| Day | Step |
|---|---|
| 0 | Payment received. Agreement signed. Baseline captured: last month's lead count, bookings and, if known, reply time. |
| 0 | Access: Meta Business Manager partner access, WhatsApp Business account and number, lead form(s), website form. |
| 1 | Facts sheet, qualifying questions, salesperson numbers, booking slots and templates drafted and **approved by the client**. Templates submitted to Meta. |
| 2 | Build from the last client's workflow (if one exists). Run the acceptance tests below. |
| 3 | Go live on **one** campaign first. Watch the first 20 conversations live. |

## Acceptance tests before go-live

- [ ] Test lead from each source → first reply within 60 s.
- [ ] Question not covered by the facts sheet → handoff, with no invented answer.
- [ ] Price question → the exact approved price, or a handoff.
- [ ] "STOP" in English, Hindi and Gujarati → suppressed.
- [ ] Hot lead → salesperson alert arrives with a correct summary.
- [ ] Invalid AI output (simulated) → safe fallback plus handoff.
- [ ] Duplicate lead (same phone twice) → one thread only.
- [ ] The weekly report generates with correct numbers from test data.

## Weekly report (what the owner sees)

| Metric | Definition |
|---|---|
| Leads | New unique leads this week, by source |
| First reply (median / slowest) | Time from lead creation to the first WhatsApp reply |
| Engaged | % of leads who replied at least once |
| Qualified | % of leads who answered all qualifying questions |
| Booked | Visits or appointments booked, compared with the baseline |
| Salesperson take-over time | Median time from alert to the salesperson's first message |
| Handoffs / AI errors | Count, plus the error rate from the transcript review |
| Opt-outs | Count |

**Customer success:** a 20-minute review on day 30 against the metric agreed at the start. The renewal decision happens in that meeting.

## Track per pilot (this is what makes it a business)

Setup hours · ongoing hours per week · LLM cost · VPS share · number of Meta templates · error rate · renewal (yes/no) · the reason for the renewal or cancellation.

## After pilot 1

Turn everything done twice into templates: a workflow export per vertical, a facts-sheet template, a template pack, the agreement and the report. The goal by client 4 is setup in under 4 hours.
