#!/usr/bin/env python3
"""Lead Response Audit.

Turns a log of test enquiries (one row per business) into:
  - summary.md         internal benchmark by vertical + prioritised list
  - reports/<slug>.html one-page audit to send to each business (optional PDF)
  - outreach/<slug>.md  WhatsApp / email / walk-in copy built from their result
  - pipeline.csv        a CRM-ready list, sorted by priority

Standard library only.

    python3 audit.py sample/audits.csv
    python3 audit.py data/audits.csv --config config.json --out out --pdf
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent

DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
)

# Upper bound (minutes) for each bucket. Anything past the audit window is NO_REPLY.
BUCKETS = (
    ("≤ 5 min", 5),
    ("5–60 min", 60),
    ("1–24 h", 24 * 60),
    ("1–7 days", 7 * 24 * 60),
)
NO_REPLY = "no reply"

FIELD_ALIASES = {
    "business": ("business", "businessname", "name", "company"),
    "vertical": ("vertical", "industry", "category"),
    "area": ("area", "city", "locality"),
    "phone": ("phone", "contactphone", "whatsapp", "number"),
    "contact_name": ("contactname", "owner", "ownername", "decisionmaker"),
    "source": ("source", "foundvia"),
    "channel": ("channel", "enquirychannel"),
    "enquiry_at": ("enquiryat", "enquirysentat", "sentat"),
    "human_response_at": ("humanresponseat", "firsthumanresponseat", "respondedat"),
    "auto_reply": ("autoreply", "autoresponse"),
    "asked_qualifying": ("askedqualifying", "qualifyingquestions"),
    "tried_to_book": ("triedtobook", "offeredbooking", "offeredvisit"),
    "followups": ("followups", "followups3d", "followupcount"),
    "notes": ("notes", "note"),
}
REQUIRED = ("business", "vertical", "channel", "enquiry_at")

VERTICAL_NAMES = {
    "real_estate": ("real-estate business", "real-estate businesses"),
    "clinic": ("clinic", "clinics"),
    "coaching": ("coaching institute", "coaching institutes"),
}

CHANNEL_NAMES = {
    "whatsapp": "WhatsApp",
    "website_form": "your website form",
    "call": "a phone call",
    "lead_form": "your lead form",
    "instagram_dm": "Instagram DM",
    "facebook_dm": "Facebook Messenger",
}

DEFAULT_CONFIG = {
    "agency": "Thrumline",
    "sender_name": "Your Name",
    "sender_phone": "",
    "sender_email": "",
    "website": "",
    "region": "your area",
    "window_days": 7,
    "followup_days": 3,
    "min_benchmark_n": 5,
    "timezone_label": "IST",
}


@dataclass
class Audit:
    row: int
    business: str
    vertical: str
    area: str
    phone: str
    contact_name: str
    source: str
    channel: str
    enquiry_at: datetime
    human_response_at: datetime | None
    auto_reply: bool | None
    asked_qualifying: bool | None
    tried_to_book: bool | None
    followups: int | None
    notes: str
    slug: str = ""
    status: str = ""  # "replied" | "no_reply" | "pending"
    minutes: float | None = None
    bucket: str = ""
    off_hours: bool = False


# ---------------------------------------------------------------- parsing

def norm_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (key or "").lower())


def parse_datetime(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised date/time {value!r} (use YYYY-MM-DD HH:MM)")


def parse_bool(value: str) -> bool | None:
    value = (value or "").strip().lower()
    if not value:
        return None
    if value in ("y", "yes", "true", "1"):
        return True
    if value in ("n", "no", "false", "0"):
        return False
    raise ValueError(f"expected yes/no, got {value!r}")


def parse_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    return int(value)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:40].strip("-") or "business"


def make_slug(business: str, area: str, phone: str) -> str:
    token = hashlib.sha256(f"{business}|{area}|{phone}".encode()).hexdigest()[:5]
    return f"{slugify(business)}-{token}"


def normalize_row(raw: dict) -> dict:
    keys = {norm_key(k): (v or "").strip() for k, v in raw.items() if isinstance(k, str) and isinstance(v, str)}
    return {field: next((keys[a] for a in aliases if keys.get(a)), "") for field, aliases in FIELD_ALIASES.items()}


def load_audits(path: Path) -> tuple[list[Audit], list[str]]:
    audits: list[Audit] = []
    errors: list[str] = []
    seen: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row_no, raw in enumerate(csv.DictReader(fh), start=2):
            rec = normalize_row(raw)
            if not any(rec.values()):
                continue
            missing = [f for f in REQUIRED if not rec[f]]
            if missing:
                errors.append(f"row {row_no}: missing {', '.join(missing)}")
                continue
            try:
                enquiry_at = parse_datetime(rec["enquiry_at"])
                response_at = parse_datetime(rec["human_response_at"])
                audit = Audit(
                    row=row_no,
                    business=rec["business"],
                    vertical=norm_vertical(rec["vertical"]),
                    area=rec["area"],
                    phone=rec["phone"],
                    contact_name=rec["contact_name"],
                    source=rec["source"],
                    channel=rec["channel"].strip().lower().replace(" ", "_"),
                    enquiry_at=enquiry_at,
                    human_response_at=response_at,
                    auto_reply=parse_bool(rec["auto_reply"]),
                    asked_qualifying=parse_bool(rec["asked_qualifying"]),
                    tried_to_book=parse_bool(rec["tried_to_book"]),
                    followups=parse_int(rec["followups"]),
                    notes=rec["notes"],
                )
            except ValueError as exc:
                errors.append(f"row {row_no}: {exc}")
                continue
            if response_at and response_at < enquiry_at:
                errors.append(f"row {row_no}: response time is before the enquiry time")
                continue
            audit.slug = make_slug(audit.business, audit.area, audit.phone)
            if audit.slug in seen:
                errors.append(f"row {row_no}: duplicate of an earlier row ({audit.business})")
                continue
            seen.add(audit.slug)
            audits.append(audit)
    return audits, errors


def norm_vertical(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


# ---------------------------------------------------------------- analysis

def classify(audit: Audit, as_of: datetime, window_days: int) -> None:
    window = window_days * 24 * 60
    audit.off_hours = audit.enquiry_at.weekday() == 6 or not 10 <= audit.enquiry_at.hour < 18
    if audit.human_response_at:
        audit.minutes = (audit.human_response_at - audit.enquiry_at).total_seconds() / 60
    if audit.minutes is not None and audit.minutes <= window:
        audit.status = "replied"
        audit.bucket = next(label for label, upper in BUCKETS if audit.minutes <= upper)
    elif audit.minutes is not None or (as_of - audit.enquiry_at).total_seconds() / 60 >= window:
        audit.status = "no_reply"
        audit.bucket = NO_REPLY
    else:
        audit.status = "pending"
        audit.bucket = ""


def rank_value(audit: Audit) -> float:
    """Lower is better. No reply ranks behind every reply."""
    return audit.minutes if audit.status == "replied" else float("inf")


def pct(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "–"


def share_true(audits: list[Audit], attr: str) -> tuple[int, int]:
    known = [getattr(a, attr) for a in audits if getattr(a, attr) is not None]
    return sum(1 for v in known if v), len(known)


def vertical_stats(audits: list[Audit]) -> dict:
    done = [a for a in audits if a.status != "pending"]
    replied = [a for a in done if a.status == "replied"]
    minutes = [a.minutes for a in replied]
    followed_up = [a for a in replied if a.followups is not None]
    return {
        "n": len(done),
        "pending": len(audits) - len(done),
        "replied": len(replied),
        "median": statistics.median(minutes) if minutes else None,
        "fastest": min(minutes) if minutes else None,
        "buckets": {label: sum(1 for a in done if a.bucket == label) for label, _ in BUCKETS + ((NO_REPLY, 0),)},
        "auto_reply": share_true(done, "auto_reply"),
        "asked_qualifying": share_true(replied, "asked_qualifying"),
        "tried_to_book": share_true(replied, "tried_to_book"),
        "followed_up": (sum(1 for a in followed_up if a.followups > 0), len(followed_up)),
        "first": min((a.enquiry_at for a in done), default=None),
        "last": max((a.enquiry_at for a in done), default=None),
    }


def faster_than_share(audit: Audit, peers: list[Audit]) -> tuple[int, int]:
    """How many other completed peers were strictly slower than this business."""
    others = [p for p in peers if p is not audit and p.status != "pending"]
    mine = rank_value(audit)
    return sum(1 for p in others if rank_value(p) > mine), len(others)


def faster_phrase(slower: int, others: int, plural: str) -> str:
    if others and slower == others:
        return f"faster than all {others} other {plural} tested"
    return f"faster than {slower} of the {others} other {plural} tested"


def priority(audit: Audit) -> str:
    if audit.status == "pending":
        return "-"
    if audit.status == "no_reply" or audit.minutes > 24 * 60:
        return "A"
    if audit.minutes > 60:
        return "B"
    return "C"


# ---------------------------------------------------------------- formatting

def fmt_duration(minutes: float | None) -> str:
    if minutes is None:
        return "–"
    if minutes < 1:
        return "under 1 min"
    minutes = round(minutes)
    if minutes < 60:
        return f"{minutes} min"
    hours, mins = divmod(minutes, 60)
    if hours < 48:
        return f"{hours} h {mins} min" if mins else f"{hours} h"
    days, hours = divmod(hours, 24)
    return f"{days} days {hours} h" if hours else f"{days} days"


def fmt_bool(value: bool | None) -> str:
    return {True: "Yes", False: "No", None: "Not recorded"}[value]


def vertical_names(vertical: str) -> tuple[str, str]:
    if vertical in VERTICAL_NAMES:
        return VERTICAL_NAMES[vertical]
    label = vertical.replace("_", " ")
    return f"{label} business", f"{label} businesses"


def channel_name(channel: str) -> str:
    return CHANNEL_NAMES.get(channel, channel.replace("_", " "))


def result_line(audit: Audit, window_days: int) -> str:
    if audit.status == "replied":
        return f"a person replied after {fmt_duration(audit.minutes)}"
    if audit.minutes is not None:
        return f"the first reply came after {fmt_duration(audit.minutes)}, outside the {window_days}-day window"
    return f"no one replied within {window_days} days"


def benchmark(audit: Audit, groups: dict[str, list[Audit]], cfg: dict) -> dict | None:
    peers = groups[audit.vertical]
    stats = vertical_stats(peers)
    if stats["n"] < cfg["min_benchmark_n"]:
        return None
    slower, others = faster_than_share(audit, peers)
    return {"stats": stats, "slower": slower, "others": others}


# ---------------------------------------------------------------- outputs

def render_report(audit: Audit, bench: dict | None, cfg: dict, today: str) -> str:
    e = html.escape
    singular, plural = vertical_names(audit.vertical)
    window = cfg["window_days"]
    if audit.status == "replied":
        headline = fmt_duration(audit.minutes)
        headline_label = "until a person first replied"
        tone = "ok" if audit.minutes <= 5 else "warn" if audit.minutes <= 60 else "bad"
    else:
        headline = "No reply"
        headline_label = f"from a person within {window} days"
        tone = "bad"

    rows = [
        ("Enquiry sent", f"{audit.enquiry_at:%d %b %Y, %H:%M} {cfg['timezone_label']} via {channel_name(audit.channel)}"),
        ("Automatic greeting received", fmt_bool(audit.auto_reply)),
    ]
    if audit.status == "replied":
        rows += [
            ("First reply from a person", f"{audit.human_response_at:%d %b %Y, %H:%M} ({fmt_duration(audit.minutes)})"),
            ("Asked about need, budget or timing", fmt_bool(audit.asked_qualifying)),
            ("Offered a visit, call or appointment", fmt_bool(audit.tried_to_book)),
        ]
        if audit.followups is not None:
            rows.append((f"Follow-ups after we went quiet ({cfg['followup_days']} days)", str(audit.followups)))
    rows_html = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in rows)

    if bench:
        s = bench["stats"]
        within5 = s["buckets"]["≤ 5 min"]
        span = f"{s['first']:%d %b} – {s['last']:%d %b %Y}"
        other_no_reply = s["buckets"][NO_REPLY] - 1
        if audit.status == "replied":
            position = f"You were {faster_phrase(bench['slower'], bench['others'], plural)}."
        elif other_no_reply:
            position = f"{other_no_reply} of the other {bench['others']} {plural} we tested did not reply either."
        else:
            position = f"Every other {singular} we tested replied."
        bench_html = f"""
<h2>How {e(plural)} in {e(cfg['region'])} compared</h2>
<p class="muted">{s['n']} {e(plural)} tested the same way, {e(span)}.</p>
<div class="stats">
  <div><b>{e(fmt_duration(s['median']))}</b><span>median time to a person's reply (among those who replied)</span></div>
  <div><b>{pct(within5, s['n'])}</b><span>replied within 5 minutes</span></div>
  <div><b>{pct(s['buckets'][NO_REPLY], s['n'])}</b><span>did not reply within {window} days</span></div>
</div>
<p>{e(position)}</p>"""
    else:
        bench_html = f"""
<h2>Local comparison</h2>
<p class="muted">Not shown yet. We only publish a comparison once at least {cfg['min_benchmark_n']} {e(plural)} have been tested, because a smaller sample would be misleading.</p>"""

    contact = " · ".join(e(x) for x in (cfg["sender_name"], cfg["sender_phone"], cfg["sender_email"]) if x)
    template = Template((HERE / "templates" / "report.html").read_text(encoding="utf-8"))
    return template.substitute(
        business=e(audit.business),
        agency=e(cfg["agency"]),
        today=e(today),
        what_we_did=e(
            f"On {audit.enquiry_at:%d %b %Y} at {audit.enquiry_at:%H:%M} {cfg['timezone_label']} we sent one enquiry "
            f"to {audit.business} via {channel_name(audit.channel)}, the way a customer would. "
            f"We recorded when a person first replied, over {window} days."
        ),
        tone=tone,
        headline=e(headline),
        headline_label=e(headline_label),
        rows=rows_html,
        benchmark=bench_html,
        contact=contact,
        window=window,
    )


def render_outreach(audit: Audit, bench: dict | None, cfg: dict) -> str:
    singular, plural = vertical_names(audit.vertical)
    greet = f"Hi {audit.contact_name.split()[0]}" if audit.contact_name else "Hi"
    when = f"{audit.enquiry_at:%d %b} at {audit.enquiry_at:%H:%M}"
    via = channel_name(audit.channel)
    window = cfg["window_days"]
    me = f"{cfg['sender_name']} from {cfg['agency']}"
    n_tested = bench["stats"]["n"] if bench else None
    study = f"a response-time study of {n_tested} {plural} in {cfg['region']}" if n_tested else f"a response-time study of {plural} in {cfg['region']}"

    if audit.status == "replied" and audit.minutes <= 60:
        hook = f"your team replied in {fmt_duration(audit.minutes)}"
        if bench:
            hook += ", " + faster_phrase(bench["slower"], bench["others"], plural)
        ask = (
            "You're clearly doing something right, so I'd like to learn how you handle leads. "
            "Would you give me 15 minutes this week? No pitch. I'll share the full local results in return."
        )
    else:
        hook = result_line(audit, window)
        context = ""
        if bench:
            stats = bench["stats"]
            if stats["fastest"] is not None:
                hook += f". The fastest {singular} I tested replied in {fmt_duration(stats['fastest'])}"
            slow = stats["n"] - stats["buckets"]["≤ 5 min"]
            if slow * 2 > stats["n"]:
                context = f" {slow} of the {stats['n']} {plural} I tested took longer than 5 minutes."
        ask = (
            f"I'm not saying this to criticise. It's one data point.{context} "
            "I've put your result and the local comparison on one page. Can I send it over?"
        )

    whatsapp = (
        f"{greet}, I'm {me}. On {when} I sent an enquiry to {audit.business} on {via} as part of {study}. "
        f"Result: {hook}.\n\n{ask}"
    )
    email_subject = f"{audit.business}: your lead response result"
    email_body = (
        f"{greet},\n\n"
        f"I'm {me}. I'm running {study}: one enquiry to each business, then I record how long it takes a person to reply.\n\n"
        f"I contacted {audit.business} on {when} via {via}. Result: {hook}.\n\n"
        f"{ask}\n\n"
        f"{cfg['sender_name']}\n{cfg['agency']}"
        + (f" · {cfg['sender_phone']}" if cfg["sender_phone"] else "")
        + (f"\n{cfg['website']}" if cfg["website"] else "")
        + "\n\nIf you'd rather not hear from me, reply \"no\" and I won't contact you again."
    )
    walk_in = (
        f"\"Hi, I'm {cfg['sender_name']}. I'm studying how quickly local {plural} reply to new enquiries. "
        f"I sent one to you on {when}; {hook}. I've printed your one-page result. "
        f"Could I get 10 minutes with whoever handles new enquiries?\""
    )
    follow_up = (
        f"{greet}, following up on the response-time result for {audit.business}. "
        "Happy to send the one-pager or go through it in 10 minutes. Either is fine. And if it's not relevant, just say so."
    )

    facts = [
        f"- Vertical: {singular}",
        f"- Area: {audit.area or '–'}",
        f"- Phone: {audit.phone or '–'}",
        f"- Channel tested: {via}",
        f"- Result: {result_line(audit, window)}",
        f"- Priority: {priority(audit)}",
    ]
    if audit.off_hours:
        facts.append("- ⚠ Enquiry was sent outside 10:00–18:00 Mon–Sat. Say so if they raise it.")
    if audit.notes:
        facts.append(f"- Notes: {audit.notes}")

    return "\n".join([
        f"# {audit.business}",
        "",
        *facts,
        "",
        "## WhatsApp (first touch)",
        "",
        whatsapp,
        "",
        "## Email",
        "",
        f"**Subject:** {email_subject}",
        "",
        email_body,
        "",
        "## Walk-in / call opener",
        "",
        walk_in,
        "",
        "## Follow-up (day 3, once)",
        "",
        follow_up,
        "",
        "## If they agree to talk",
        "",
        "Run the discovery questions in `docs/sales/validation-sprint.md`. Learn first, pitch last.",
        "",
    ])


def render_summary(audits: list[Audit], groups: dict[str, list[Audit]], cfg: dict, errors: list[str], as_of: datetime) -> str:
    lines = [
        "# Lead Response Audit: summary (internal)",
        "",
        f"Generated {as_of:%d %b %Y %H:%M}. Window: {cfg['window_days']} days. "
        f"Benchmarks shown to prospects only when n ≥ {cfg['min_benchmark_n']}.",
        "",
        "These are your own measurements. Report them as measured; do not round them up into claims.",
        "",
    ]
    header = "| Vertical | Tested | Pending | Median reply (repliers only) | ≤ 5 min | 5–60 min | 1–24 h | 1–7 days | No reply | Auto-greeting | Asked qualifying* | Offered booking* | Followed up* |"
    lines += [header, "|" + "---|" * (header.count("|") - 1)]
    for vertical, peers in sorted(groups.items()):
        s = vertical_stats(peers)
        b = s["buckets"]
        lines.append(
            f"| {vertical_names(vertical)[1]} | {s['n']} | {s['pending']} | {fmt_duration(s['median'])} | "
            + " | ".join(f"{b[label]} ({pct(b[label], s['n'])})" for label in [l for l, _ in BUCKETS] + [NO_REPLY])
            + f" | {pct(*s['auto_reply'])} | {pct(*s['asked_qualifying'])} | {pct(*s['tried_to_book'])} | {pct(*s['followed_up'])} |"
        )
    lines += ["", "\\* share of businesses that replied, where recorded.", ""]

    off = sum(1 for a in audits if a.off_hours)
    if off:
        noun = "enquiry was" if off == 1 else "enquiries were"
        lines += [f"⚠ {off} {noun} sent outside 10:00–18:00 Mon–Sat. Their times are included but are not a fair comparison.", ""]

    lines += ["## Pipeline by priority", "", "A = no reply or > 24 h · B = 1–24 h · C = ≤ 1 h (learn from them; weak prospects)", ""]
    lines += ["| Priority | Business | Vertical | Area | Result |", "|---|---|---|---|---|"]
    for a in sorted(audits, key=lambda a: (priority(a) == "-", priority(a), -rank_value(a), a.business)):
        lines.append(f"| {priority(a)} | {a.business} | {vertical_names(a.vertical)[0]} | {a.area or '–'} | {result_line(a, cfg['window_days']) if a.status != 'pending' else 'pending'} |")
    if errors:
        lines += ["", "## Rows skipped", ""] + [f"- {err}" for err in errors]
    return "\n".join(lines) + "\n"


def write_pipeline(path: Path, audits: list[Audit], cfg: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["priority", "slug", "business", "vertical", "area", "contact_name", "phone", "result",
                         "status", "last_contact", "next_action", "next_action_date", "notes"])
        for a in sorted(audits, key=lambda a: (priority(a) == "-", priority(a), a.business)):
            writer.writerow([
                priority(a), a.slug, a.business, a.vertical, a.area, a.contact_name, a.phone,
                result_line(a, cfg["window_days"]) if a.status != "pending" else "pending",
                "new" if a.status != "pending" else "audit pending",
                "", "send audit result" if a.status != "pending" else "wait for audit window", "", "",
            ])


def find_browser(explicit: str | None) -> str | None:
    candidates = [explicit, os.environ.get("CHROME_PATH"), "google-chrome", "google-chrome-stable",
                  "chromium", "chromium-browser", "chrome", "msedge"]
    for cand in filter(None, candidates):
        found = shutil.which(cand) or (cand if Path(cand).is_file() else None)
        if found:
            return found
    return None


def export_pdf(browser: str, html_path: Path) -> bool:
    pdf_path = html_path.with_suffix(".pdf")
    cmd = [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    return result.returncode == 0 and pdf_path.exists()


def load_config(path: Path | None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path is None:
        path = HERE / "config.json"
        if not path.exists():
            path = HERE / "config.example.json"
            print(f"note: no config.json, using {path.name}. Copy it to config.json and add your details.", file=sys.stderr)
    cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg


def run(csv_path: Path, out_dir: Path, cfg: dict, as_of: datetime, pdf: bool = False, browser: str | None = None) -> dict:
    audits, errors = load_audits(csv_path)
    for audit in audits:
        classify(audit, as_of, cfg["window_days"])
    groups: dict[str, list[Audit]] = {}
    for audit in audits:
        groups.setdefault(audit.vertical, []).append(audit)

    (out_dir / "reports").mkdir(parents=True, exist_ok=True)
    (out_dir / "outreach").mkdir(parents=True, exist_ok=True)
    today = f"{as_of:%d %b %Y}"
    browser_path = find_browser(browser) if pdf else None
    if pdf and not browser_path:
        print("warning: --pdf requested but no Chrome/Chromium found; pass --browser PATH", file=sys.stderr)

    written = 0
    for audit in audits:
        if audit.status == "pending":
            continue
        bench = benchmark(audit, groups, cfg)
        report = out_dir / "reports" / f"{audit.slug}.html"
        report.write_text(render_report(audit, bench, cfg, today), encoding="utf-8")
        if browser_path and not export_pdf(browser_path, report):
            print(f"warning: PDF export failed for {report.name}", file=sys.stderr)
        (out_dir / "outreach" / f"{audit.slug}.md").write_text(render_outreach(audit, bench, cfg), encoding="utf-8")
        written += 1

    (out_dir / "summary.md").write_text(render_summary(audits, groups, cfg, errors, as_of), encoding="utf-8")
    write_pipeline(out_dir / "pipeline.csv", audits, cfg)
    return {"audits": len(audits), "reports": written, "pending": sum(a.status == "pending" for a in audits), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", type=Path, help="audit log CSV (see sample/audits.csv)")
    parser.add_argument("--out", type=Path, default=HERE / "out", help="output folder (default: ./out)")
    parser.add_argument("--config", type=Path, help="config JSON (default: config.json, else config.example.json)")
    parser.add_argument("--as-of", help="treat this as 'now' (YYYY-MM-DD HH:MM); default: current time")
    parser.add_argument("--pdf", action="store_true", help="also export each report to PDF with headless Chrome")
    parser.add_argument("--browser", help="path to Chrome/Chromium for --pdf")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    as_of = parse_datetime(args.as_of) if args.as_of else datetime.now().replace(second=0, microsecond=0)
    result = run(args.csv, args.out, cfg, as_of, pdf=args.pdf, browser=args.browser)
    for err in result["errors"]:
        print(f"skipped {err}", file=sys.stderr)
    print(f"{result['audits']} audits read, {result['reports']} reports written, "
          f"{result['pending']} still inside the audit window. Output: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
