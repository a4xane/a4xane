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
CFG = dict(audit.DEFAULT_CONFIG, region="Testville")


def write_csv(text: str) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


def make(business="Biz", minutes=None, enquiry=datetime(2026, 9, 8, 11, 0), vertical="clinic") -> audit.Audit:
    response = None if minutes is None else enquiry + timedelta(minutes=minutes)
    a = audit.Audit(row=2, business=business, vertical=vertical, area="", phone="", contact_name="", source="",
                    channel="whatsapp", enquiry_at=enquiry, human_response_at=response, auto_reply=None,
                    asked_qualifying=None, tried_to_book=None, followups=None, notes="")
    a.slug = audit.make_slug(business, "", "")
    audit.classify(a, AS_OF, 7)
    return a


class ParsingTests(unittest.TestCase):
    def test_header_aliases_and_case(self):
        rec = audit.normalize_row({"Business Name": "X", "Industry": "Clinic", "Sent At": "2026-09-08 10:00", "Channel": "WhatsApp"})
        self.assertEqual((rec["business"], rec["vertical"], rec["enquiry_at"]), ("X", "Clinic", "2026-09-08 10:00"))

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


class OutputTests(unittest.TestCase):
    def groups(self, audits):
        g = {}
        for a in audits:
            g.setdefault(a.vertical, []).append(a)
        return g

    def test_benchmark_hidden_below_minimum_sample(self):
        peers = [make(f"B{i}", 10) for i in range(4)]
        self.assertIsNone(audit.benchmark(peers[0], self.groups(peers), CFG))
        html = audit.render_report(peers[0], None, CFG, "24 Sep 2026")
        self.assertIn("Not shown yet", html)

    def test_benchmark_shown_at_minimum_sample(self):
        peers = [make(f"B{i}", 10 * (i + 1)) for i in range(5)]
        bench = audit.benchmark(peers[0], self.groups(peers), CFG)
        self.assertEqual(bench["stats"]["n"], 5)
        html = audit.render_report(peers[0], bench, CFG, "24 Sep 2026")
        self.assertIn("faster than all 4 other clinics tested", html)

    def test_report_escapes_csv_content(self):
        a = make("<script>alert(1)</script>", 3)
        html = audit.render_report(a, None, CFG, "24 Sep 2026")
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_outreach_only_claims_majority_when_true(self):
        fast = [make(f"F{i}", 2) for i in range(4)]
        slow = make("Slow", None)
        peers = fast + [slow]
        bench = audit.benchmark(slow, self.groups(peers), CFG)
        text = audit.render_outreach(slow, bench, CFG)
        self.assertNotIn("took longer than 5 minutes", text)
        self.assertIn("The fastest clinic I tested replied in 2 min", text)

        slow_peers = [make(f"S{i}", 120) for i in range(4)] + [make("Slow", None)]
        bench = audit.benchmark(slow_peers[-1], self.groups(slow_peers), CFG)
        self.assertIn("5 of the 5 clinics I tested took longer than 5 minutes", audit.render_outreach(slow_peers[-1], bench, CFG))

    def test_fast_responder_gets_learning_ask_not_pitch(self):
        a = make("Quick", 3)
        text = audit.render_outreach(a, None, CFG)
        self.assertIn("your team replied in 3 min", text)
        self.assertIn("No pitch", text)

    def test_end_to_end_on_sample(self):
        sample = Path(audit.HERE) / "sample" / "audits.csv"
        with tempfile.TemporaryDirectory() as out:
            result = audit.run(sample, Path(out), CFG, AS_OF)
            self.assertEqual((result["audits"], result["reports"], result["pending"], result["errors"]), (16, 15, 1, []))
            rows = list(csv.DictReader(io.StringIO((Path(out) / "pipeline.csv").read_text(encoding="utf-8"))))
            self.assertEqual(rows[0]["priority"], "A")
            self.assertEqual(rows[-1]["status"], "audit pending")
            summary = (Path(out) / "summary.md").read_text(encoding="utf-8")
            self.assertIn("1 enquiry was sent outside", summary)


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
