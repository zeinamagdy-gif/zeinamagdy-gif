#!/usr/bin/env python3
"""Build assets/heartbeat.svg from your real GitHub contributions.

Usage:
  GH_TOKEN=<token> GH_LOGIN=zeinamagdy-gif python scripts/build_heartbeat.py
  python scripts/build_heartbeat.py --sample   # fake data, only to preview the design
  python scripts/build_heartbeat.py --empty    # all zeros (placeholder)

Needs only the Python standard library. If the GitHub request fails, the script
exits with an error and leaves the existing SVG untouched (it never invents data).
"""
import json
import math
import os
import random
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DAYS = 60
OUT = Path(__file__).resolve().parent.parent / "assets" / "heartbeat.svg"

MONO = "'JetBrains Mono','SFMono-Regular','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_counts(login, token, start, end):
    """Return {date: contributions} for the window, straight from GitHub."""
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
            "from": start.strftime("%Y-%m-%dT00:00:00Z"),
            "to": end.strftime("%Y-%m-%dT23:59:59Z"),
        },
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "heartbeat-readme"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors") or not (payload.get("data") or {}).get("user"):
        raise RuntimeError(f"GitHub API error: {payload.get('errors') or 'user not found'}")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def compute(counts_by_date, today):
    days = [today - timedelta(days=DAYS - 1 - i) for i in range(DAYS)]
    counts = [int(counts_by_date.get(d.isoformat(), 0)) for d in days]

    bpm = sum(counts[-7:])                       # contributions in the last 7 days
    last30 = sum(counts[-30:])
    active = sum(1 for c in counts if c > 0)

    streak, i = 0, DAYS - 1
    if counts[i] == 0:                           # today isn't over yet: start from yesterday
        i -= 1
    while i >= 0 and counts[i] > 0:
        streak += 1
        i -= 1

    peak = max(counts)
    peak_day = days[counts.index(peak)] if peak else None
    return days, counts, dict(bpm=bpm, last30=last30, active=active, streak=streak,
                              peak=peak, peak_day=peak_day)


def heartbeat_path(counts):
    """A flat line with one ECG beat on every day that has contributions."""
    step = 808 / DAYS
    peak = max(counts) or 1
    beat = [0.14, 0.24, 0.32, 0.42, 0.50, 0.58, 0.66, 0.795, 0.90, 1.0]
    pts = ["M36 216"]
    for i, c in enumerate(counts):
        x0 = 36 + i * step
        if c == 0:
            pts.append(f"L{x0 + step:.1f} 216.0")
            continue
        a = 0.22 + 0.78 * math.sqrt(c / peak)    # taller beat = busier day
        ys = [216, 212, 216, 216 + 15.4 * a, 216 - 96 * a, 216 + 26.9 * a, 216, 210, 216, 216]
        for f, y in zip(beat, ys):
            pts.append(f"L{x0 + f * step:.1f} {y:.1f}")
    return " ".join(pts)


def stat(x, delay, label, value):
    return f'''<g transform="translate({x} 70)" opacity="0"><animate attributeName="opacity" begin="{delay}s" dur=".5s" to="1" fill="freeze"/>
  <animateTransform attributeName="transform" type="translate" begin="{delay}s" dur=".5s" from="0 6" to="0 0" fill="freeze" additive="sum" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/>
  <text font-family="{MONO}" font-size="10.5" letter-spacing="1.2" fill="#75757C">{label}</text>
  <text y="30" font-family="{SANS}" font-size="26" font-weight="800" fill="#F2F2F2">{value}</text>
</g>'''


def render(days, counts, s):
    d = heartbeat_path(counts)
    peak_label = f"PEAK · {s['peak_day'].strftime('%b').upper()} {s['peak_day'].day}" if s["peak_day"] else "PEAK"
    start_label = f"{days[0].strftime('%b')} {days[0].day}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="280" viewBox="0 0 880 280" fill="none" role="img" aria-label="Heartbeat of my public GitHub contributions over the last {DAYS} days">
<defs>
  <filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <pattern id="grid-s" width="12" height="12" patternUnits="userSpaceOnUse"><path d="M12 0H0V12" stroke="#F2F2F2" stroke-opacity=".025"/></pattern>
<pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="60" height="60" fill="url(#grid-s)"/><path d="M60 0H0V60" stroke="#F2F2F2" stroke-opacity=".055"/></pattern>
</defs>
<rect x=".5" y=".5" width="879" height="279" rx="16" fill="#0B0B0D" stroke="#232329"/>
<circle cx="24" cy="22" r="5" fill="#3A3A40"/><circle cx="41" cy="22" r="5" fill="#3A3A40"/><circle cx="58" cy="22" r="5" fill="#3A3A40"/>
<text x="76" y="26" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="#75757C">HEARTBEAT · {DAYS} DAYS OF PUBLIC CONTRIBUTIONS</text>
<circle cx="816" cy="22" r="3.5" fill="#B8FF6B" fill-opacity=".35"><animate attributeName="r" values="3.5;9.1" dur="1.6s" repeatCount="indefinite"/><animate attributeName="fill-opacity" values=".45;0" dur="1.6s" repeatCount="indefinite"/></circle>
<circle cx="816" cy="22" r="3.5" fill="#B8FF6B"/><text x="858" y="26" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="#B8FF6B">LIVE</text>
<line x1="1" y1="44.5" x2="879" y2="44.5" stroke="#232329"/>
<rect x="1" y="110" width="878" height="134" fill="url(#grid)"/>
<g transform="translate(36 70)">
  <text font-family="{MONO}" font-size="10.5" letter-spacing="1.2" fill="#75757C">BPM*</text>
  <g transform="translate(9 20)"><g>
    <animateTransform attributeName="transform" type="scale" values="1;1.28;1;1.14;1" keyTimes="0;.15;.3;.45;1" dur="1s" repeatCount="indefinite"/>
    <path d="M0 3.2C0-1 5.5-2.2 7 1.6 8.5-2.2 14-1 14 3.2 14 7.4 7 11.5 7 11.5S0 7.4 0 3.2z" transform="translate(-7 -5)" fill="#B8FF6B"/>
  </g></g>
  <text x="28" y="31" font-family="{SANS}" font-size="34" font-weight="800" fill="#B8FF6B">{s['bpm']}</text>
</g>
{stat(236, "0.20", "LAST 30 DAYS", s['last30'])}
{stat(396, "0.32", "ACTIVE DAYS", f"{s['active']}/{DAYS}")}
{stat(556, "0.44", "STREAK", f"{s['streak']}d")}
{stat(716, "0.56", peak_label, s['peak'])}
<path d="{d}" pathLength="1000" stroke="#B3B3B8" stroke-width="1.8" stroke-linejoin="round" stroke-dasharray="1000" stroke-dashoffset="1000">
  <animate attributeName="stroke-dashoffset" begin=".3s" dur="2.4s" to="0" fill="freeze"/>
</path>
<path d="{d}" pathLength="1000" stroke="#B8FF6B" stroke-width="2.6" stroke-linejoin="round" stroke-dasharray="0 1000" filter="url(#glow)">
  <animate attributeName="stroke-dasharray" begin="2.7s" dur=".01s" to="34 966" fill="freeze"/>
  <animate attributeName="stroke-dashoffset" begin="2.7s" dur="3.6s" from="34" to="-966" repeatCount="indefinite"/>
</path>
<text x="36" y="264" font-family="{MONO}" font-size="11" fill="#75757C">{start_label}</text>
<text x="440" y="264" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#3A3A40">* bpm = contributions in the last 7 days</text>
<text x="844" y="264" text-anchor="end" font-family="{MONO}" font-size="11" fill="#75757C">today</text>
</svg>
'''


def main():
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=DAYS - 1)

    if "--sample" in sys.argv:
        random.seed(7)
        data = {(start + timedelta(days=i)).isoformat(): (random.choice([0, 0, 1, 3, 8, 15, 40]))
                for i in range(DAYS)}
    elif "--empty" in sys.argv:
        data = {}
    else:
        token = os.environ.get("GH_TOKEN")
        login = os.environ.get("GH_LOGIN", "zeinamagdy-gif")
        if not token:
            sys.exit("GH_TOKEN is not set; refusing to draw data I can't verify.")
        data = fetch_counts(login, token, start, today)

    days, counts, stats = compute(data, today)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(days, counts, stats), encoding="utf-8")
    print(f"wrote {OUT} | last 7d={stats['bpm']} last30={stats['last30']} "
          f"active={stats['active']}/{DAYS} streak={stats['streak']} peak={stats['peak']}")


if __name__ == "__main__":
    main()
