# Lead Response Audit tool

Status: **PROTOTYPE**. Works on sample data. It has not been used on real businesses yet.

It turns your log of test enquiries into the outreach assets for the validation sprint (`docs/sales/validation-sprint.md`):

| Output | What it is | Who sees it |
|---|---|---|
| `out/summary.md` | Benchmarks by vertical and a list sorted by priority | You only |
| `out/reports/<slug>.html` (+ `.pdf` with `--pdf`) | A one-page result for one business | That business |
| `out/outreach/<slug>.md` | WhatsApp, email, walk-in and follow-up copy built from their result | You (send it yourself) |
| `out/pipeline.csv` | CRM-ready list; import it into Google Sheets or HubSpot. When you re-run the tool, your edits to `status`, `last_contact`, `next_action`, `next_action_date` and `notes` are kept. | You only |

It uses only the Python standard library (3.10+). There is nothing to install.

## Run it

```bash
cd tools/response-audit
cp config.example.json config.json        # add your name, number, email, city
python3 audit.py sample/audits.csv --as-of "2026-09-24 12:00" --allow-placeholders   # demo data
python3 audit.py data/audits.csv --pdf    # your real log; --pdf needs Chrome/Chromium
python3 -m unittest discover -s tests     # 32 tests
```

Keep real data in `tools/response-audit/data/`. Both that folder and `out/` are gitignored, **because this repository is public**. Never commit real business or lead data here. If you pass an `--out` folder that git would pick up, the tool prints a warning.

The tool refuses to run while `config.json` still has placeholder contact details (`Your Name`, `XXXXX`, `yourdomain`, `your city`), because they would appear in every report and message. `--allow-placeholders` is only for demo runs, and output from a demo run must never be sent.

## The log (one row per business)

| Column | Required | Example | Notes |
|---|---|---|---|
| business | yes | Example Homes | |
| vertical | yes | real_estate | `real_estate`, `clinic` and `coaching` have friendly names. Any other value also works. |
| area | | Station Road | |
| phone | | +91 98xxx xxxxx | the business's public number |
| contact_name | | Dr. Mehta | the first name is used in the greeting (honorifics are kept: "Hi Dr. Mehta") |
| source | | meta_ad_library | where you found them |
| channel | yes | whatsapp | `whatsapp`, `website_form`, `call`, `instagram_dm`, `facebook_dm` |
| enquiry_at | yes | 2026-09-29 11:05 | when you sent the enquiry (`YYYY-MM-DD HH:MM`) |
| auto_reply | | yes | did an automatic greeting arrive? |
| human_response_at | | 2026-09-29 13:40 | the first reply **from a person**. Leave it blank if nobody replied. |
| asked_qualifying | | yes | did they ask about your need, budget or timing? |
| tried_to_book | | no | did they offer a visit, call or appointment? |
| followups | | 1 | messages or calls from them in the 3 days after their first reply, while you stayed quiet |
| notes | | | |

Rules the tool applies:
- No reply from a person within `window_days` (default 3, the same as the disclosure deadline) counts as **no reply**. A blank response inside the window counts as **pending**.
- **Benchmarks and the summary only count audits whose window has closed.** Fast replies arrive before silent rows mature, so counting them early would make a vertical look better than it is. A fast replier still gets its report straight away.
- Enquiries sent outside Mon–Sat 10:00–18:00 are flagged. That comparison is not fair, so avoid them.
- A business is only compared with the local benchmark once at least `min_benchmark_n` (default 5) businesses in its vertical are complete. Smaller samples are not shown, and the outreach then doesn't mention a comparison.
- Outreach only uses anonymised totals about other businesses (e.g. "2 of the other 5 replied within 5 minutes"), never one competitor's individual time.
- Duplicates are detected ignoring case, spacing and phone formatting.
- Each run clears `out/reports` and `out/outreach` first, so files for deleted rows can't be sent by mistake. Cells in `pipeline.csv` that start with `+ = - @` are prefixed with `'`, so spreadsheets read them as text, not formulas.
- Priority: **A** means no reply or over 24 h, **B** means 1–24 h, **C** means 1 h or less. C businesses get a request to learn from them, not a pitch.
