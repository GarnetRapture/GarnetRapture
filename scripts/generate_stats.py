import os
import sys
import json
import urllib.request
from urllib.error import URLError

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    print("GITHUB_TOKEN is missing")
    sys.exit(1)

QUERY = """
query {
  viewer {
    repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode("utf-8"),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
except URLError as e:
    print("Failed to fetch data:", e)
    sys.exit(1)

langs = {}
repos = data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])
for repo in repos:
    edges = repo.get("languages", {}).get("edges", [])
    for edge in edges:
        name = edge["node"]["name"]
        color = edge["node"]["color"] or "#cccccc"
        size = edge["size"]
        if name not in langs:
            langs[name] = {"size": 0, "color": color}
        langs[name]["size"] += size

sorted_langs = sorted(langs.items(), key=lambda x: x[1]["size"], reverse=True)[:5]
total_size = sum(x[1]["size"] for x in sorted_langs)

svg_width = 300
svg_height = 140
svg = f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" fill="none" xmlns="http://www.w3.org/2000/svg">'
svg += '<style>.lang-name { font: 600 12px "Segoe UI", Ubuntu, Sans-Serif; fill: #c9d1d9; } .lang-percent { font: 400 12px "Segoe UI", Ubuntu, Sans-Serif; fill: #8b949e; }</style>'
svg += f'<rect width="{svg_width}" height="{svg_height}" fill="#0d1117" rx="4.5" stroke="#30363d"/>'
svg += '<text x="15" y="25" fill="#58a6ff" font-family="sans-serif" font-weight="bold" font-size="14">Top Languages</text>'

y_pos = 45
for lang_name, lang_data in sorted_langs:
    percent = (lang_data["size"] / total_size) * 100 if total_size > 0 else 0
    color = lang_data["color"]
    svg += f'<circle cx="20" cy="{y_pos-4}" r="5" fill="{color}"/>'
    svg += f'<text x="35" y="{y_pos}" class="lang-name">{lang_name}</text>'
    svg += f'<text x="125" y="{y_pos}" class="lang-percent">{percent:.1f}%</text>'
    
    bar_width = 110
    fill_width = (percent / 100) * bar_width
    svg += f'<rect x="175" y="{y_pos-8}" width="{bar_width}" height="8" fill="#21262d" rx="4"/>'
    svg += f'<rect x="175" y="{y_pos-8}" width="{fill_width}" height="8" fill="{color}" rx="4"/>'
    
    y_pos += 20

svg += '</svg>'

os.makedirs("assets", exist_ok=True)
with open("assets/top-langs.svg", "w", encoding="utf-8") as f:
    f.write(svg)
