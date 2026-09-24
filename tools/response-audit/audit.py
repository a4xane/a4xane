#!/usr/bin/env python3
"""Lead Response Audit.

Turns a log of test enquiries (one row per business) into:
  - summary.md         internal benchmark by vertical + prioritised list
  - reports/<slug>.html one-page audit to send to each business (optional PDF)
  - outreach/<slug>.md  WhatsApp / email / walk-in copy built from their result
  - pipeline.csv        a CRM-ready list, sorted by priority (your edits are kept)

Standard library only.

    python3 audit.py sample/audits.csv --allow-placeholders
    python3 audit.py data/audits.csv --pdf
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

FAST = "≤ 5 min"
# Upper bound (minutes) of each reply bucket; reply_buckets() adds a final one up to the audit window.
FIXED_BUCKETS = (
    (FAST, 5),
    ("5–60 min", 60),
    ("1–24 h", 24 * 60),
)
NO_REPLY = "no reply"

FIELD_ALIASES = {
    "business": ("business", "businessname", "company", "companyname"),
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

HONORIFICS = {"dr", "mr", "mrs", "ms", "miss", "shri", "smt", "prof", "adv", "er", "ca"}

DEFAULT_CONFIG = {
    "agency": "Thrumline",
    "sender_name": "Your Name",
    "sender_phone": "",
    "sender_email": "",
    "website": "",
    "region": "your area",
    "window_days": 3,
    "followup_days": 3,
    "min_benchmark_n": 5,
    "timezone_label": "IST",
}
PLACEHOLDER_MARKERS = ("your name", "xxxxx", "yourdomain", "your city", "your area")

PIPELINE_FIELDS = ["priority", "slug", "business", "vertical", "area", "contact_name", "phone", "result",
                   "status", "last_contact", "next_action", "next_action_date", "notes"]
# Columns you maintain by hand. A re-run keeps your values; only the tool's own defaults are refreshed.
MANUAL_FIELDS = ("status", "last_contact", "next_action", "next_action_date", "notes")
AUTO_VALUES = {
    "status": {"new", "audit pending"},
    "next_action": {"send audit result", "wait for audit window"},
}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


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
    matured: bool = False  # the audit window has closed, so the result is final and can enter benchmarks
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
    """Stable id; ignores case, spacing and phone formatting so re-typed duplicates collide."""
    norm = lambda s: " ".join(s.lower().split())  # noqa: E731
    key = f"{norm(business)}|{norm(area)}|{re.sub(r'[^0-9]', '', phone)}"
    token = hashlib.sha256(key.encode()).hexdigest()[:5]
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

def reply_buckets(window_days: int) -> tuple[tuple[str, int], ...]:
    window = window_days * 24 * 60
    buckets = [(label, upper) for label, upper in FIXED_BUCKETS if upper <= window]
    if window > FIXED_BUCKETS[-1][1]:
        buckets.append((f"1–{window_days} days", window))
    return tuple(buckets)


def bucket_labels(window_days: int) -> list[str]:
    return [label for label, _ in reply_buckets(window_days)] + [NO_REPLY]


def classify(audit: Audit, as_of: datetime, window_days: int) -> None:
    window = window_days * 24 * 60
    audit.off_hours = audit.enquiry_at.weekday() == 6 or not 10 <= audit.enquiry_at.hour < 18
    if audit.human_response_at:
        audit.minutes = (audit.human_response_at - audit.enquiry_at).total_seconds() / 60
    elapsed = (as_of - audit.enquiry_at).total_seconds() / 60
    audit.matured = elapsed >= window or (audit.minutes is not None and audit.minutes > window)
    if audit.minutes is not None and audit.minutes <= window:
        audit.status = "replied"
        audit.bucket = next(label for label, upper in reply_buckets(window_days) if audit.minutes <= upper)
    elif audit.matured:
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


def vertical_stats(audits: list[Audit], window_days: int) -> dict:
    """Stats over matured audits only. Counting early replies before silent rows mature would flatter the vertical."""
    done = [a for a in audits if a.matured]
    replied = [a for a in done if a.status == "replied"]
    minutes = [a.minutes for a in replied]
    followed_up = [a for a in replied if a.followups is not None]
    return {
        "n": len(done),
        "open": len(audits) - len(done),
        "replied": len(replied),
        "median": statistics.median(minutes) if minutes else None,
        "buckets": {label: sum(1 for a in done if a.bucket == label) for label in bucket_labels(window_days)},
        "auto_reply": share_true(done, "auto_reply"),
        "asked_qualifying": share_true(replied, "asked_qualifying"),
        "tried_to_book": share_true(replied, "tried_to_book"),
        "followed_up": (sum(1 for a in followed_up if a.followups > 0), len(followed_up)),
        "first": min((a.enquiry_at for a in done), default=None),
        "last": max((a.enquiry_at for a in done), default=None),
    }


def matured_others(audit: Audit, peers: list[Audit]) -> list[Audit]:
    return [p for p in peers if p is not audit and p.matured]


def faster_than_share(audit: Audit, peers: list[Audit]) -> tuple[int, int]:
    """How many other matured peers were strictly slower than this business."""
    others = matured_others(audit, peers)
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


def greeting(contact_name: str) -> str:
    parts = contact_name.split()
    if not parts:
        return "Hi"
    if parts[0].rstrip(".").lower() in HONORIFICS and len(parts) > 1:
        return f"Hi {parts[0]} {parts[-1]}"
    return f"Hi {parts[0]}"


def result_line(audit: Audit, window_days: int) -> str:
    if audit.status == "replied":
        return f"a person replied after {fmt_duration(audit.minutes)}"
    if audit.minutes is not None:
        return f"the first reply came after {fmt_duration(audit.minutes)}, outside the {window_days}-day window"
    return f"no one replied within {window_days} days"


def benchmark(audit: Audit, groups: dict[str, list[Audit]], cfg: dict) -> dict | None:
    peers = groups[audit.vertical]
    stats = vertical_stats(peers, cfg["window_days"])
    if stats["n"] < cfg["min_benchmark_n"]:
        return None
    others = matured_others(audit, peers)
    slower, _ = faster_than_share(audit, peers)
    return {
        "stats": stats,
        "slower": slower,
        "others": len(others),
        "others_fast": sum(1 for p in others if p.bucket == FAST),
        "others_no_reply": sum(1 for p in others if p.status == "no_reply"),
    }


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
        span = f"{s['first']:%d %b} – {s['last']:%d %b %Y}"
        if audit.status == "replied" and bench["slower"]:
            position = f"You were {faster_phrase(bench['slower'], bench['others'], plural)}."
        elif audit.status == "replied":
            position = f"The other {bench['others']} {plural} we tested all replied at least as fast."
        elif bench["others_no_reply"]:
            position = f"{bench['others_no_reply']} of the other {bench['others']} {plural} we tested did not reply either."
        else:
            position = f"Every other {singular} we tested replied."
        bench_html = f"""
<h2>How {e(plural)} in {e(cfg['region'])} compared</h2>
<p class="muted">{s['n']} {e(plural)} tested the same way, {e(span)}.</p>
<div class="stats">
  <div><b>{e(fmt_duration(s['median']))}</b><span>median time to a person's reply (among those who replied)</span></div>
  <div><b>{pct(s['buckets'][FAST], s['n'])}</b><span>replied within 5 minutes</span></div>
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
    )


def render_outreach(audit: Audit, bench: dict | None, cfg: dict) -> str:
    singular, plural = vertical_names(audit.vertical)
    greet = greeting(audit.contact_name)
    when = f"{audit.enquiry_at:%d %b} at {audit.enquiry_at:%H:%M}"
    via = channel_name(audit.channel)
    window = cfg["window_days"]
    me = f"{cfg['sender_name']} from {cfg['agency']}"
    n_tested = bench["stats"]["n"] if bench else None
    study = f"a response-time study of {n_tested} {plural} in {cfg['region']}" if n_tested else f"a response-time study of {plural} in {cfg['region']}"

    # Only anonymised totals about other businesses: never one competitor's individual result.
    if audit.status == "replied" and audit.minutes <= 60:
        hook = f"your team replied in {fmt_duration(audit.minutes)}"
        if bench and bench["slower"]:
            hook += ", " + faster_phrase(bench["slower"], bench["others"], plural)
        ask = (
            "You're clearly doing something right, so I'd like to learn how you handle leads. "
            "Would you give me 15 minutes this week? No pitch. I'll share the local results in return."
        )
    else:
        hook = result_line(audit, window)
        context = ""
        if bench:
            if bench["others_fast"]:
                hook += f". {bench['others_fast']} of the other {bench['others']} {plural} I tested replied within 5 minutes"
            stats = bench["stats"]
            slow = stats["n"] - stats["buckets"][FAST]
            if slow * 2 > stats["n"]:
                context = f" {slow} of the {stats['n']} {plural} I tested took longer than 5 minutes."
        page = "your result and the local comparison" if bench else "your result"
        ask = (
            f"I'm not saying this to criticise. It's one data point.{context} "
            f"I've put {page} on one page. Can I send it over?"
        )

    whatsapp = (
        f"{greet}, I'm {me}. On {when} I sent an enquiry to {audit.business} via {via} as part of {study}. "
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
    window = cfg["window_days"]
    labels = bucket_labels(window)
    lines = [
        "# Lead Response Audit: summary (internal)",
        "",
        f"Generated {as_of:%d %b %Y %H:%M}. Window: {window} days. Only audits whose window has closed are counted, "
        f"so early replies can't flatter a vertical. Benchmarks are shown to prospects only when n ≥ {cfg['min_benchmark_n']}.",
        "",
        "These are your own measurements. Report them as measured; do not round them up into claims.",
        "",
    ]
    header = ("| Vertical | Complete | Window open | Median reply (repliers only) | "
              + " | ".join(labels)
              + " | Auto-greeting | Asked qualifying* | Offered booking* | Followed up* |")
    lines += [header, "|" + "---|" * (header.count("|") - 1)]
    for vertical, peers in sorted(groups.items()):
        s = vertical_stats(peers, window)
        b = s["buckets"]
        lines.append(
            f"| {vertical_names(vertical)[1]} | {s['n']} | {s['open']} | {fmt_duration(s['median'])} | "
            + " | ".join(f"{b[label]} ({pct(b[label], s['n'])})" for label in labels)
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
        lines.append(f"| {priority(a)} | {a.business} | {vertical_names(a.vertical)[0]} | {a.area or '–'} | {result_line(a, window) if a.status != 'pending' else 'pending'} |")
    if errors:
        lines += ["", "## Rows skipped", ""] + [f"- {err}" for err in errors]
    return "\n".join(lines) + "\n"


def sheet_safe(value: str) -> str:
    """Stop spreadsheets from reading a cell as a formula (CSV injection; also keeps '+91 …' phones intact)."""
    return "'" + value if value.startswith(FORMULA_PREFIXES) else value


def sheet_unsafe(value: str) -> str:
    return value[1:] if value.startswith("'") and value[1:].startswith(FORMULA_PREFIXES) else value


def write_pipeline(path: Path, audits: list[Audit], cfg: dict) -> None:
    """Rewrite pipeline.csv from the audit log, keeping the columns you edit by hand.

    Rows whose business is no longer in the audit log are dropped (e.g. someone asked to be left out).
    """
    previous: dict[str, dict] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as fh:
            previous = {row["slug"]: row for row in csv.DictReader(fh) if row.get("slug")}

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(PIPELINE_FIELDS)
        for a in sorted(audits, key=lambda a: (priority(a) == "-", priority(a), a.business)):
            done = a.status != "pending"
            row = {
                "priority": priority(a), "slug": a.slug, "business": a.business, "vertical": a.vertical,
                "area": a.area, "contact_name": a.contact_name, "phone": a.phone,
                "result": result_line(a, cfg["window_days"]) if done else "pending",
                "status": "new" if done else "audit pending",
                "last_contact": "",
                "next_action": "send audit result" if done else "wait for audit window",
                "next_action_date": "", "notes": "",
            }
            kept = previous.get(a.slug, {})
            for field in MANUAL_FIELDS:
                old = sheet_unsafe((kept.get(field) or "").strip())
                if old and old not in AUTO_VALUES.get(field, ()):
                    row[field] = old
            writer.writerow([sheet_safe(str(row[f])) for f in PIPELINE_FIELDS])


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
    pdf_path.unlink(missing_ok=True)
    cmd = [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0 and pdf_path.exists()


def clear_generated(out_dir: Path) -> None:
    """Remove last run's reports/outreach so files for deleted rows can't be sent by mistake."""
    for sub in ("reports", "outreach"):
        folder = out_dir / sub
        folder.mkdir(parents=True, exist_ok=True)
        for f in folder.iterdir():
            if f.is_file() and f.suffix in (".html", ".pdf", ".md"):
                f.unlink()


def warn_if_publishable(out_dir: Path) -> None:
    """This repo is public: shout if the output folder would be picked up by `git add`."""
    try:
        inside = subprocess.run(["git", "-C", str(out_dir), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, timeout=10)
        if inside.stdout.strip() != "true":
            return
        ignored = subprocess.run(["git", "-C", str(out_dir), "check-ignore", "-q", "reports/probe.html"],
                                 capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return
    if ignored.returncode != 0:
        print(f"WARNING: {out_dir} is inside a git repository and NOT gitignored. It contains real business data; "
              "do not commit it. Use the default output folder or add it to .gitignore.", file=sys.stderr)


def placeholder_fields(cfg: dict) -> list[str]:
    return [k for k in ("sender_name", "sender_phone", "sender_email", "region")
            if any(m in str(cfg.get(k, "")).lower() for m in PLACEHOLDER_MARKERS)]


def load_config(path: Path | None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path is None:
        path = HERE / "config.json"
        if not path.exists():
            path = HERE / "config.example.json"
            print(f"note: no config.json, using {path.name}. Copy it to config.json and add your details.", file=sys.stderr)
    cfg.update(json.loads(path.read_text(encoding="utf-8")))
    for key in ("window_days", "followup_days", "min_benchmark_n"):
        if not isinstance(cfg[key], int) or cfg[key] < 1:
            raise ValueError(f"config {key} must be a whole number ≥ 1, got {cfg[key]!r}")
    return cfg


def run(csv_path: Path, out_dir: Path, cfg: dict, as_of: datetime, pdf: bool = False, browser: str | None = None) -> dict:
    audits, errors = load_audits(csv_path)
    for audit in audits:
        classify(audit, as_of, cfg["window_days"])
    groups: dict[str, list[Audit]] = {}
    for audit in audits:
        groups.setdefault(audit.vertical, []).append(audit)

    clear_generated(out_dir)
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
    parser.add_argument("--out", type=Path, default=HERE / "out", help="output folder (default: tools/response-audit/out)")
    parser.add_argument("--config", type=Path, help="config JSON (default: config.json, else config.example.json)")
    parser.add_argument("--as-of", help="treat this as 'now' (YYYY-MM-DD HH:MM); default: current time")
    parser.add_argument("--pdf", action="store_true", help="also export each report to PDF with headless Chrome")
    parser.add_argument("--browser", help="path to Chrome/Chromium for --pdf")
    parser.add_argument("--allow-placeholders", action="store_true",
                        help="run even though config still has placeholder contact details (demo only; never send the output)")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    placeholders = placeholder_fields(cfg)
    if placeholders and not args.allow_placeholders:
        print(f"error: config still has placeholder values for {', '.join(placeholders)}. They would appear in every "
              "report and message. Fill in config.json, or pass --allow-placeholders for a demo run.", file=sys.stderr)
        return 2
    as_of = parse_datetime(args.as_of) if args.as_of else datetime.now().replace(second=0, microsecond=0)
    args.out.mkdir(parents=True, exist_ok=True)
    warn_if_publishable(args.out)
    result = run(args.csv, args.out, cfg, as_of, pdf=args.pdf, browser=args.browser)
    for err in result["errors"]:
        print(f"skipped {err}", file=sys.stderr)
    print(f"{result['audits']} audits read, {result['reports']} reports written, "
          f"{result['pending']} still inside the audit window. Output: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
