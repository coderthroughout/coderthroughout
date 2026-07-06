#!/usr/bin/env python3
"""Refresh the stats sentence in README.md between <!-- stats --> markers."""
import json, os, re, urllib.request

QUERY = """{ user(login: "coderthroughout") { contributionsCollection {
  restrictedContributionsCount
  contributionCalendar { totalContributions } } } }"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
             "Content-Type": "application/json"})
cc = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]

total = cc["contributionCalendar"]["totalContributions"]
private = cc["restrictedContributionsCount"]
pct = round(private / total * 100) if total else 0

if pct >= 50:
    sentence = (f"**{total:,}** contributions in the last year — **{pct}%** of it "
                f"heads-down in omium’s private repos.")
else:
    sentence = f"**{total:,}** contributions in the last year."

readme = open("README.md").read()
updated = re.sub(r"<!-- stats -->.*?<!-- /stats -->",
                 f"<!-- stats -->{sentence}<!-- /stats -->", readme, flags=re.S)
if updated != readme:
    open("README.md", "w").write(updated)
    print("updated:", sentence)
else:
    print("no change")
