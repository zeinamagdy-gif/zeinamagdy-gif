"""Generate heartbeat.svg from your real public GitHub contributions (last 60 days)."""
import datetime as dt
import json
import os
import urllib.request

LOGIN = os.environ.get("GH_LOGIN", "zeinamagdy-gif")
DAYS = 60
MONO = "'JetBrains Mono','SFMono-Regular','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){contributionsCollection(from:$from,to:$to){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def fetch_counts():
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=DAYS - 1)
    body = json.dumps({"query": QUERY, "variables": {
        "login": LOGIN, "from": f"{start}T00:00:00Z", "to": f"{today}T23:59:59Z"}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"],
                 "Content-Type": "application/json", "User-Agent": "heartbeat-svg"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in data:
        raise RuntimeError(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    by_day = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    return [by_day.get(str(start + dt.timedelta(days=i)), 0) for i in range(DAYS)], start


def stat(x, label, value, delay):
    return (f'<g transform="translate({x} 70)" opacity="0">'
            f'<animate attributeName="opacity" begin="{delay}s" dur=".5s" to="1" fill="freeze"/>'
            f'<text font-family="{MONO}" font-size="10.5" letter-spacing="1.2" fill="#75757C">{label}</text>'
            f'<text y="30" font-family="{SANS}" font-size="26" font-weight="800" fill="#F2F2F2">{value}</text></g>')


def render(counts, start):
    bpm = sum(counts[-7:])
    last30 = sum(counts[-30:])
    active = sum(1 for c in counts if c > 0)
    peak = max(counts)
    streak = 0
    for c in reversed(counts[:-1] if counts[-1] == 0 else counts):  # today may still be empty
        if c == 0:
            break
        streak += 1

    base, max_h, step = 216, 88, 808 / (DAYS - 1)
    pts = []
    for i, c in enumerate(counts):
        x = 36 + i * step
        if c > 0:
            h = 22 + (max_h - 22) * c / peak
            pts += [(x - 4, base), (x - 2, base + 6), (x, base - h), (x + 2, base + 14), (x + 4, base)]
        else:
            pts.append((x, base))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    start_label = f"{start:%b} {start.day}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="280" viewBox="0 0 880 280" fill="none" role="img" aria-label="Heartbeat of my public GitHub contributions over the last 60 days">
<defs>
  <filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <pattern id="grid-s" width="12" height="12" patternUnits="userSpaceOnUse"><path d="M12 0H0V12" stroke="#F2F2F2" stroke-opacity=".025"/></pattern>
  <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="60" height="60" fill="url(#grid-s)"/><path d="M60 0H0V60" stroke="#F2F2F2" stroke-opacity=".055"/></pattern>
</defs>
<rect x=".5" y=".5" width="879" height="279" rx="16" fill="#0B0B0D" stroke="#232329"/>
<circle cx="24" cy="22" r="5" fill="#3A3A40"/><circle cx="41" cy="22" r="5" fill="#3A3A40"/><circle cx="58" cy="22" r="5" fill="#3A3A40"/>
<text x="76" y="26" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="#75757C">HEARTBEAT · 60 DAYS OF PUBLIC CONTRIBUTIONS</text>
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
  <text x="28" y="31" font-family="{SANS}" font-size="34" font-weight="800" fill="#B8FF6B">{bpm}</text>
</g>
{stat(236, "LAST 30 DAYS", last30, "0.2")}
{stat(396, "ACTIVE DAYS", f"{active}/{DAYS}", "0.32")}
{stat(556, "STREAK", f"{streak}d", "0.44")}
{stat(716, "PEAK", peak, "0.56")}
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


if __name__ == "__main__":
    counts, start = fetch_counts()
    with open("heartbeat.svg", "w", encoding="utf-8") as f:
        f.write(render(counts, start))
    print(f"Wrote heartbeat.svg ({sum(counts)} contributions in {DAYS} days)")
