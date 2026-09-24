# CLAUDE.md

Read this first in every session. Then read `DECISIONS.md` and `TODO.md`.

## This repository is PUBLIC

`a4xane/a4xane` is a GitHub **profile** repository. Anyone can read it.
- **Do not replace the root `README.md`.** It is the public GitHub profile page.
- **Never commit** personal details, client or lead data, audit logs, credentials or `.env` files. Real data lives in gitignored folders (`tools/response-audit/data/`, `out/`, `config.json`).
- The founder's full master context (background, history, past projects) is kept **outside** this repo on purpose. Ask the founder for it if a task needs it. Don't paste it here.
- Exception (D-006): the founder's name (Kanish Shah) and business WhatsApp (+91 83470 55841) appear in `site/` because a business website needs a contact. Don't add other personal details.
- Planned move: a private repo for the business (`TODO.md`). Until then, keep this repo to non-sensitive strategy, docs and tools.

## Current objective

Validate the **Lead Response System** thesis (`docs/strategy/lead-response-thesis.md`): WhatsApp speed-to-lead, qualification and booking for local businesses that pay for leads. It is sold under Thrumline.
**Status: EXPLORING.** No customer conversations, pilots or revenue yet. Don't describe it as more than that.

Next milestone: the 14-day validation sprint (`docs/sales/validation-sprint.md`). **GO gate:** ≥ 3 paid pilots from ≤ 30 conversations.

## Rules for Claude in this repo

1. **Evidence before engineering.** No delivery software before the first paid pilot. No dashboard or SaaS before 3 clients renew (D-003). If asked to build ahead of the gates, say so and ask the founder to confirm.
2. **Label every number** as a fact (with source and date), an assumption, a projection or an illustration. Never write "we will make ₹X". Write "under assumption Y, revenue would be ₹X".
3. **Don't invent** sources, customers, results or quotes. If something can't be verified, say "I cannot confirm this."
4. **Verify before quoting:** WhatsApp/Meta pricing and policy change often. Update `docs/research/sources.md` with the date checked.
5. **Decisions go in `DECISIONS.md`** (DATE / DECISION / WHY / ALTERNATIVES / EVIDENCE / CONSEQUENCES / STATUS). The founder makes decisions; Claude proposes.
6. **Priorities:** revenue work > validation > client delivery > evidence-based improvements > pipeline > automation > branding > nice-to-haves.
7. **Project status labels:** IDEA, EXPLORING, VALIDATING, PROTOTYPE, MVP, PILOT, PAID, ACTIVE, SCALING, PAUSED, ARCHIVED. Existing files don't make a project ACTIVE.
8. **Historical projects** (FLUX, Quote-to-Cash, AI Business Analyst, CPA Conversion System, DRIFT) stay parked unless the founder reactivates them.

## Map

```text
CLAUDE.md                      this file
DECISIONS.md                   decision log
TODO.md                        next actions, owner, status
docs/strategy/                 lead-response-thesis.md (full framework: market → scale, economics, risks)
docs/sales/                    validation-sprint.md (list, audit protocol, outreach, discovery, close), pilot-agreement.md
docs/operations/               pilot-spec.md (delivery architecture, guardrails, onboarding, report). SPEC ONLY
docs/research/                 sources.md (every external claim, its source and how well it is verified)
tools/response-audit/          audit log → benchmarks, one-page reports, outreach copy, pipeline.csv
brand/                         BRAND.md (positioning, voice, colours, type), mark/logo SVG, png/ social assets, src/ export source
site/                          the Thrumline website (static HTML, self-hosted fonts): index.html, privacy.html. NOT DEPLOYED yet
docs/marketing/                launch-plan.md (zero-budget channels, 14-day calendar), content.md (ready-to-post copy)
```

## Commands

```bash
cd tools/response-audit
python3 audit.py sample/audits.csv --as-of "2026-09-24 12:00" --allow-placeholders   # demo run → ./out
python3 audit.py data/audits.csv --pdf                          # real run (data/ is gitignored)
python3 -m unittest discover -s tests                           # must pass before committing
```

Conventions: tools use the Python standard library only (3.10+) and `unittest`. Generated client-facing copy must stay factual: report only what was measured, and show comparisons only when n ≥ 5.
