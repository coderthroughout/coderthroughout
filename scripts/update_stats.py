#!/usr/bin/env python3
"""Daily refresh: stats sentence between <!-- stats --> markers in README.md,
plus assets/v2/heatmap-{dark,light}.svg — a contribution heatmap in the
profile's own design language. Fonts come pre-subsetted from assets/fonts/."""
import base64, json, os, re, urllib.request

LOGIN = "coderthroughout"

QUERY = """{ user(login: "%s") { contributionsCollection {
  restrictedContributionsCount
  contributionCalendar { totalContributions
    weeks { contributionDays { date contributionCount } } } } } }""" % LOGIN

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
             "Content-Type": "application/json"})
cc = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]
cal = cc["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]
private = cc["restrictedContributionsCount"]
pct = round(private / total * 100) if total else 0

days = [d for w in weeks for d in w["contributionDays"]]
best = cur = 0
for d in days:
    cur = cur + 1 if d["contributionCount"] > 0 else 0
    best = max(best, cur)

# ---------------------------------------------------------------- sentence
if pct >= 50:
    sentence = (f"**{total:,}** contributions in the last year — **{pct}%** of it "
                f"heads-down in omium’s private repos.")
else:
    sentence = f"**{total:,}** contributions in the last year."

readme = open("README.md").read()
updated = re.sub(r"<!-- stats -->\n?.*?\n?<!-- /stats -->",
                 f"<!-- stats -->\n{sentence}\n<!-- /stats -->", readme, flags=re.S)
if updated != readme:
    open("README.md", "w").write(updated)
    print("sentence:", sentence)

# ---------------------------------------------------------------- heatmap
def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()

MONO_B64 = b64("assets/fonts/mono.woff2")
SG_B64 = b64("assets/fonts/grotesk.woff2")

PALETTES = dict(
    dark=dict(bg="#0A0A0B", fg="#F2F2ED", muted="#85858A", faint="#232326",
              empty="#19191C", scale=["0.22", "0.42", "0.68", "1"], accent="#C8FF4D"),
    light=dict(bg="#FAFAF7", fg="#141414", muted="#73736E", faint="#E5E5DF",
               empty="#ECECE6", scale=["0.28", "0.5", "0.72", "1"], accent="#557F00"),
)

# intensity thresholds relative to the year's max day
mx = max((d["contributionCount"] for d in days), default=1) or 1

def level(c):
    if c == 0: return -1
    r = c / mx
    return 0 if r <= 0.25 else 1 if r <= 0.5 else 2 if r <= 0.75 else 3

CELL, GAP, X0, Y0 = 20, 6, 64, 84
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]

def heatmap(p):
    faces = (f"@font-face{{font-family:'JBM';src:url(data:font/woff2;base64,{MONO_B64}) format('woff2');}}"
             f"@font-face{{font-family:'SG';font-weight:700;src:url(data:font/woff2;base64,{SG_B64}) format('woff2');}}")
    mono = "font-family=\"'JBM','JetBrains Mono',ui-monospace,monospace\""
    sg = "font-family=\"'SG','Space Grotesk',system-ui,sans-serif\" font-weight=\"700\""
    cells, labels = [], []
    last_month = None
    for wi, w in enumerate(weeks):
        x = X0 + wi * (CELL + GAP)
        m = int(w["contributionDays"][0]["date"][5:7]) - 1
        if m != last_month and wi < len(weeks) - 2:
            labels.append(f'<text x="{x}" y="52" {mono} font-size="18" fill="{p["muted"]}">{MONTHS[m]}</text>')
            last_month = m
        for d in w["contributionDays"]:
            wd = __import__("datetime").date.fromisoformat(d["date"]).weekday()
            row = (wd + 1) % 7  # sunday first, like github
            y = Y0 + row * (CELL + GAP)
            lv = level(d["contributionCount"])
            if lv < 0:
                cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="5" fill="{p["empty"]}"/>')
            else:
                cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="5" '
                             f'fill="{p["accent"]}" fill-opacity="{p["scale"][lv]}"/>')
    grid_h = 7 * (CELL + GAP) - GAP
    by = Y0 + grid_h + 52
    H = by + 28
    return f'''<svg width="1600" height="{H}" viewBox="0 0 1600 {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{total:,} contributions in the last year, peak {mx} in a single day">
<style>{faces}</style>
<rect x="1" y="1" width="1598" height="{H-2}" rx="24" fill="{p['bg']}"/>
<rect x="1" y="1" width="1598" height="{H-2}" rx="24" fill="none" stroke="{p['faint']}" stroke-width="2"/>
{"".join(labels)}
{"".join(cells)}
<text x="64" y="{by}" {sg} font-size="40" letter-spacing="-1" fill="{p['fg']}">{total:,}</text>
<text x="{64 + int(40 * 0.62 * len(f'{total:,}')) + 26}" y="{by}" {mono} font-size="22" fill="{p['muted']}">contributions in the last year · peak {mx} in a single day</text>
<text x="1536" y="{by}" {mono} font-size="20" fill="{p['muted']}" text-anchor="end">updated daily</text>
</svg>'''

os.makedirs("assets/v2", exist_ok=True)
for name, pal in PALETTES.items():
    with open(f"assets/v2/heatmap-{name}.svg", "w") as f:
        f.write(heatmap(pal))
print(f"heatmap: total={total:,} best_streak={best} max_day={mx}")
