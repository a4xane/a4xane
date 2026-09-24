import contextlib
import csv
import io
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import audit  # noqa: E402

HEADER = "business,vertical,area,phone,channel,enquiry_at,auto_reply,human_response_at,asked_qualifying,tried_to_book,followups,notes\n"
AS_OF = datetime(2026, 9, 24, 12, 0)
CFG = dict(audit.DEFAULT_CONFIG, region="Testville", window_days=7)
SAMPLE = Path(audit.HERE) / "sample" / "audits.csv"


def write_csv(text: str) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


def make(business="Biz", minutes=None, enquiry=datetime(2026, 9, 8, 11, 0), vertical="clinic",
         as_of=AS_OF, window_days=7, contact_name="") -> audit.Audit:
    response = None if minutes is None else enquiry + timedelta(minutes=minutes)
    a = audit.Audit(row=2, business=business, vertical=vertical, area="", phone="", contact_name=contact_name,
                    source="", channel="whatsapp", enquiry_at=enquiry, human_response_at=response, auto_reply=None,
                    asked_qualifying=None, tried_to_book=None, followups=None, notes="")
    a.slug = audit.make_slug(business, "", "")
    audit.classify(a, as_of, window_days)
    return a


def groups(audits):
    g = {}
    for a in audits:
        g.setdefault(a.vertical, []).append(a)
    return g


class ParsingTests(unittest.TestCase):
    def test_header_aliases_and_case(self):
        rec = audit.normalize_row({"Business Name": "X", "Industry": "Clinic", "Sent At": "2026-09-08 10:00", "Channel": "WhatsApp"})
        self.assertEqual((rec["business"], rec["vertical"], rec["enquiry_at"]), ("X", "Clinic", "2026-09-08 10:00"))

    def test_person_name_column_is_not_taken_as_business(self):
        rec = audit.normalize_row({"Name": "Priya Sharma", "Company": "Acme Dental"})
        self.assertEqual(rec["business"], "Acme Dental")

    def test_extra_csv_columns_are_ignored(self):
        rec = audit.normalize_row({"business": "X", None: ["overflow"]})
        self.assertEqual(rec["business"], "X")

    def test_datetime_formats(self):
        self.assertEqual(audit.parse_datetime("08/09/2026 14:05"), datetime(2026, 9, 8, 14, 5))
        self.assertIsNone(audit.parse_datetime(""))
        with self.assertRaises(ValueError):
            audit.parse_datetime("yesterday")

    def test_bad_rows_are_reported_not_fatal(self):
        path = write_csv(HEADER
                         + "Good,clinic,,,whatsapp,2026-09-08 11:00,,2026-09-08 11:03,,,,\n"
                         + ",clinic,,,whatsapp,2026-09-08 11:00,,,,,,\n"
                         + "Backwards,clinic,,,whatsapp,2026-09-08 11:00,,2026-09-08 10:00,,,,\n"
                         + "Maybe,clinic,,,whatsapp,2026-09-08 11:00,perhaps,,,,,\n"
                         + "Good,clinic,,,whatsapp,2026-09-09 11:00,,,,,,\n")
        audits, errors = audit.load_audits(path)
        self.assertEqual([a.business for a in audits], ["Good"])
        self.assertEqual(len(errors), 4)
        self.assertIn("missing business", errors[0])
        self.assertIn("before the enquiry", errors[1])
        self.assertIn("yes/no", errors[2])
        self.assertIn("duplicate", errors[3])

    def test_duplicates_ignore_case_spacing_and_phone_format(self):
        path = write_csv(HEADER
                         + "Demo Realty,real_estate,Area A,+91 98765 43210,whatsapp,2026-09-08 11:00,,,,,,\n"
                         + "demo  realty,real_estate,area a,+919876543210,whatsapp,2026-09-09 11:00,,,,,,\n")
        audits, errors = audit.load_audits(path)
        self.assertEqual(len(audits), 1)
        self.assertIn("duplicate", errors[0])

    def test_slug_is_ascii_and_stable(self):
        slug = audit.make_slug("Café Ünïcode & Co", "Area", "1")
        self.assertRegex(slug, r"^cafe-unicode-co-[0-9a-f]{5}$")
        self.assertEqual(slug, audit.make_slug("Café Ünïcode & Co", "Area", "1"))


class ClassificationTests(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(make(minutes=0).bucket, "≤ 5 min")
        self.assertEqual(make(minutes=5).bucket, "≤ 5 min")
        self.assertEqual(make(minutes=6).bucket, "5–60 min")
        self.assertEqual(make(minutes=60 * 5).bucket, "1–24 h")
        self.assertEqual(make(minutes=60 * 30).bucket, "1–7 days")

    def test_long_window_does_not_crash(self):
        a = make(minutes=60 * 24 * 8, window_days=14, as_of=datetime(2026, 9, 30, 12, 0))
        self.assertEqual((a.status, a.bucket), ("replied", "1–14 days"))

    def test_one_day_window_has_no_multi_day_bucket(self):
        self.assertEqual(audit.bucket_labels(1), ["≤ 5 min", "5–60 min", "1–24 h", "no reply"])

    def test_no_reply_after_window(self):
        a = make(minutes=None)
        self.assertEqual((a.status, a.bucket), ("no_reply", audit.NO_REPLY))

    def test_reply_after_window_counts_as_no_reply(self):
        a = make(minutes=60 * 24 * 8)
        self.assertEqual(a.status, "no_reply")
        self.assertIn("outside the 7-day window", audit.result_line(a, 7))

    def test_pending_inside_window(self):
        a = make(minutes=None, enquiry=datetime(2026, 9, 21, 11, 0))
        self.assertEqual(a.status, "pending")
        self.assertEqual(audit.priority(a), "-")

    def test_off_hours_flag(self):
        self.assertTrue(make(enquiry=datetime(2026, 9, 8, 19, 30), minutes=3).off_hours)
        self.assertTrue(make(enquiry=datetime(2026, 9, 13, 11, 0), minutes=3).off_hours)  # Sunday
        self.assertFalse(make(enquiry=datetime(2026, 9, 8, 11, 0), minutes=3).off_hours)

    def test_priority(self):
        self.assertEqual(audit.priority(make(minutes=None)), "A")
        self.assertEqual(audit.priority(make(minutes=60 * 25)), "A")
        self.assertEqual(audit.priority(make(minutes=90)), "B")
        self.assertEqual(audit.priority(make(minutes=30)), "C")

    def test_faster_than_counts_no_reply_as_slowest(self):
        peers = [make("A", 2), make("B", 30), make("C", None), make("D", 30)]
        self.assertEqual(audit.faster_than_share(peers[1], peers), (1, 3))  # tie with D is not "faster"
        self.assertEqual(audit.faster_than_share(peers[0], peers), (3, 3))

    def test_mid_window_run_does_not_flatter_fast_repliers(self):
        # Day 5 of the sprint: enquiries sent 2 days ago, 5 fast replies in, 15 still silent.
        sent = datetime(2026, 9, 22, 11, 0)
        day5 = datetime(2026, 9, 24, 12, 0)
        cohort = [make(f"F{i}", 3, sent, as_of=day5, window_days=3) for i in range(5)]
        cohort += [make(f"S{i}", None, sent, as_of=day5, window_days=3) for i in range(15)]
        stats = audit.vertical_stats(cohort, 3)
        self.assertEqual((stats["n"], stats["open"]), (0, 20))
        self.assertIsNone(audit.benchmark(cohort[0], groups(cohort), dict(CFG, window_days=3)))

        later = datetime(2026, 9, 26, 12, 0)
        for a in cohort:
            audit.classify(a, later, 3)
        stats = audit.vertical_stats(cohort, 3)
        self.assertEqual((stats["n"], stats["buckets"]["≤ 5 min"], stats["buckets"][audit.NO_REPLY]), (20, 5, 15))


class OutputTests(unittest.TestCase):
    def test_benchmark_hidden_below_minimum_sample(self):
        peers = [make(f"B{i}", 10) for i in range(4)]
        self.assertIsNone(audit.benchmark(peers[0], groups(peers), CFG))
        html = audit.render_report(peers[0], None, CFG, "24 Sep 2026")
        self.assertIn("Not shown yet", html)

    def test_benchmark_shown_at_minimum_sample(self):
        peers = [make(f"B{i}", 10 * (i + 1)) for i in range(5)]
        bench = audit.benchmark(peers[0], groups(peers), CFG)
        self.assertEqual(bench["stats"]["n"], 5)
        html = audit.render_report(peers[0], bench, CFG, "24 Sep 2026")
        self.assertIn("faster than all 4 other clinics tested", html)

    def test_slowest_replier_is_not_told_faster_than_zero(self):
        peers = [make(f"Q{i}", 2) for i in range(4)] + [make("Late", 50)]
        bench = audit.benchmark(peers[-1], groups(peers), CFG)
        text = audit.render_outreach(peers[-1], bench, CFG)
        self.assertNotIn("faster than 0", text)
        self.assertIn("all replied at least as fast", audit.render_report(peers[-1], bench, CFG, "x"))

    def test_report_escapes_csv_content(self):
        a = make("<script>alert(1)</script>", 3)
        html = audit.render_report(a, None, CFG, "24 Sep 2026")
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_outreach_uses_only_anonymised_totals(self):
        fast = [make(f"F{i}", 2) for i in range(4)]
        slow = make("Slow", None)
        bench = audit.benchmark(slow, groups(fast + [slow]), CFG)
        text = audit.render_outreach(slow, bench, CFG)
        self.assertNotIn("fastest", text)
        self.assertIn("4 of the other 4 clinics I tested replied within 5 minutes", text)
        self.assertNotIn("took longer than 5 minutes", text)  # not a majority, so not claimed

        slow_peers = [make(f"S{i}", 120) for i in range(4)] + [make("Slow", None)]
        bench = audit.benchmark(slow_peers[-1], groups(slow_peers), CFG)
        text = audit.render_outreach(slow_peers[-1], bench, CFG)
        self.assertIn("5 of the 5 clinics I tested took longer than 5 minutes", text)
        self.assertNotIn("replied within 5 minutes", text)

    def test_outreach_does_not_promise_a_comparison_that_is_hidden(self):
        text = audit.render_outreach(make("Slow", None), None, CFG)
        self.assertIn("I've put your result on one page", text)
        self.assertNotIn("comparison", text)

    def test_fast_responder_gets_learning_ask_not_pitch(self):
        text = audit.render_outreach(make("Quick", 3), None, CFG)
        self.assertIn("your team replied in 3 min", text)
        self.assertIn("No pitch", text)

    def test_greeting_keeps_honorific_with_surname(self):
        self.assertEqual(audit.greeting("Dr. Mehta"), "Hi Dr. Mehta")
        self.assertEqual(audit.greeting("Priya Shah"), "Hi Priya")
        self.assertEqual(audit.greeting(""), "Hi")

    def test_sheet_safe_blocks_formulas(self):
        self.assertEqual(audit.sheet_safe("=HYPERLINK(\"x\")"), "'=HYPERLINK(\"x\")")
        self.assertEqual(audit.sheet_safe("+91 98765 43210"), "'+91 98765 43210")
        self.assertEqual(audit.sheet_safe("Acme"), "Acme")
        self.assertEqual(audit.sheet_unsafe("'+91 1"), "+91 1")
        self.assertEqual(audit.sheet_unsafe("'quoted note"), "'quoted note")

    def test_pdf_export_failure_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "r.html"
            report.write_text("<p>x</p>")
            stale = report.with_suffix(".pdf")
            stale.write_text("old")
            self.assertFalse(audit.export_pdf(str(Path(tmp) / "no-such-chrome"), report))
            self.assertFalse(stale.exists())

    def test_end_to_end_on_sample(self):
        cfg = dict(CFG, window_days=3)
        with tempfile.TemporaryDirectory() as out:
            result = audit.run(SAMPLE, Path(out), cfg, AS_OF)
            self.assertEqual((result["audits"], result["reports"], result["pending"], result["errors"]), (16, 15, 1, []))
            rows = list(csv.DictReader(io.StringIO((Path(out) / "pipeline.csv").read_text(encoding="utf-8"))))
            self.assertEqual(rows[0]["priority"], "A")
            self.assertEqual(rows[-1]["status"], "audit pending")
            self.assertTrue(all(r["phone"].startswith("'+91") for r in rows))
            summary = (Path(out) / "summary.md").read_text(encoding="utf-8")
            self.assertIn("1 enquiry was sent outside", summary)
            self.assertIn("1–3 days", summary)

    def test_rerun_keeps_manual_pipeline_edits_and_clears_stale_files(self):
        cfg = dict(CFG, window_days=3)
        with tempfile.TemporaryDirectory() as out:
            out = Path(out)
            audit.run(SAMPLE, out, cfg, AS_OF)
            path = out / "pipeline.csv"
            rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
            target = next(r for r in rows if r["business"] == "Demo Realty 03")
            target.update(status="pilot proposed", notes="=owner keen; call Monday", next_action="send agreement")
            pending = next(r for r in rows if r["business"] == "Demo Realty 07")
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=audit.PIPELINE_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            (out / "reports" / "deleted-business-00000.html").write_text("stale")

            audit.run(SAMPLE, out, cfg, datetime(2026, 9, 26, 12, 0))  # Demo Realty 07's window has now closed
            rows = {r["business"]: r for r in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))}
            self.assertEqual(rows["Demo Realty 03"]["status"], "pilot proposed")
            self.assertEqual(rows["Demo Realty 03"]["next_action"], "send agreement")
            self.assertEqual(rows["Demo Realty 03"]["notes"], "'=owner keen; call Monday")
            self.assertEqual(pending["status"], "audit pending")
            self.assertEqual(rows["Demo Realty 07"]["status"], "new")
            self.assertFalse((out / "reports" / "deleted-business-00000.html").exists())


class ConfigTests(unittest.TestCase):
    def test_placeholder_config_blocks_real_runs(self):
        with tempfile.TemporaryDirectory() as out:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = audit.main([str(SAMPLE), "--out", out, "--config", str(audit.HERE / "config.example.json")])
            self.assertEqual(code, 2)
            self.assertIn("placeholder", err.getvalue())
            self.assertFalse((Path(out) / "summary.md").exists())
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                code = audit.main([str(SAMPLE), "--out", out, "--config", str(audit.HERE / "config.example.json"),
                                   "--as-of", "2026-09-24 12:00", "--allow-placeholders"])
            self.assertEqual(code, 0)

    def test_invalid_window_is_rejected(self):
        path = write_csv('{"window_days": 0}')
        with self.assertRaises(ValueError):
            audit.load_config(path)


class FormattingTests(unittest.TestCase):
    def test_durations(self):
        self.assertEqual(audit.fmt_duration(0.4), "under 1 min")
        self.assertEqual(audit.fmt_duration(59), "59 min")
        self.assertEqual(audit.fmt_duration(120), "2 h")
        self.assertEqual(audit.fmt_duration(125), "2 h 5 min")
        self.assertEqual(audit.fmt_duration(60 * 50), "2 days 2 h")
        self.assertEqual(audit.fmt_duration(None), "–")


if __name__ == "__main__":
    unittest.main()
