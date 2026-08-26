#!/usr/bin/env python3
"""
Generates a pixel-perfect terminal-style GitHub profile card (dark.svg + light.svg).

Features:
- Perfectly centered vector Sakura branch art and balanced layout.
- Modern terminal aesthetics with macOS window controls & animated blinking prompt.
- Live stats integration with GitHub API.
"""

import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
import numpy as np
from PIL import Image

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
USERNAME = "jemin-023"
IMAGE_ASSET = "assets/cherry_blossom.png"

INFO = [
    ("__header__", "Jemin Morabiya", ""),
    ("__rule__", "", ""),
    ("Education", "Indian Institute of Information Technology, Pune", "val"),
    ("__blank__", "", ""),
    ("__section__", "~/stack", ""),
    ("Lang",     "C · C++ · Python · Rust · Bash", "val"),
    ("AI / ML",  "PyTorch · JAX · OpenCV · CuPy · NumPy", "val"),
    ("Data",     "Pandas · Polars · Matplotlib · Seaborn", "val"),
    ("Embedded", "ESP32 · Arduino · Raspberry Pi", "val"),
    ("Systems",  "Arch Linux · Ubuntu · Mint · Windows", "val"),
    ("Tools",    "Git · Docker · n8n · Obsidian", "val"),
    ("__blank__", "", ""),
    ("__section__", "~/highlights", ""),
    ("WebForge '26", "🥉 3rd Place · Manipal University Jaipur", "warn"),
    ("Biothon '26",  "Finalist · India's Biggest Biology Hackathon", "warn"),
    ("__stats__", "", ""),
    ("__blank__", "", ""),
    ("__section__", "~/reach", ""),
    ("LinkedIn", "linkedin.com/in/jemin-morabiya-339852368", "accent"),
    ("Kaggle",   "kaggle.com/jeminm", "accent"),
    ("LeetCode", "leetcode.com/u/C76gNljs1T", "accent"),
    ("Mail",     "jeminmorabiyawork@gmail.com", "accent"),
]

THEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "border": "#30363d",
        "text": "#c9d1d9", "muted": "#8b949e", "key": "#38bdf8",
        "accent": "#f472b6", "warn": "#fbbf24", "prompt": "#34d399",
        "dot1": "#ff5f56", "dot2": "#ffbd2e", "dot3": "#27c93f",
        "bark": "#5c242c",
        "core": "#7c2847",
        "petal_mid": "#dc7aa0",
        "petal_light": "#f8afcc",
    },
    "light": {
        "bg": "#ffffff", "panel": "#fbf2f6", "border": "#e5d5de",
        "text": "#1f2328", "muted": "#656d76", "key": "#0284c7",
        "accent": "#db2777", "warn": "#d97706", "prompt": "#059669",
        "dot1": "#ff5f56", "dot2": "#ffbd2e", "dot3": "#27c93f",
        "bark": "#4e1a20",
        "core": "#6a1f3c",
        "petal_mid": "#d96f98",
        "petal_light": "#f29ec0",
    },
}

W, H = 980, 580
PIXEL_SIZE = 9.4
GRID_W, GRID_H = 37, 30
# Center art in the left pane (width ~ 400px) and align vertically with info block
ART_OX = 36
ART_OY = 120
INFO_X, INFO_Y, INFO_LH = 420, 94, 17.5
VAL_X = INFO_X + 96


# ----------------------------------------------------------------------------
# PIXEL ART RENDERER
# ----------------------------------------------------------------------------
def render_pixel_art(colors):
    img_path = Path(__file__).parent / IMAGE_ASSET
    if not img_path.exists():
        return ""

    img = Image.open(img_path).convert("RGBA")
    arr = np.asarray(img)

    is_white = (arr[:, :, 0] > 235) & (arr[:, :, 1] > 235) & (arr[:, :, 2] > 235)
    is_trans = arr[:, :, 3] < 50
    mask = ~(is_white | is_trans)

    ys, xs = np.nonzero(mask)
    if len(xs) == 0 or len(ys) == 0:
        return ""

    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    cropped = img.crop((x0, y0, x1 + 1, y1 + 1))
    small = cropped.resize((GRID_W, GRID_H), Image.Resampling.NEAREST)
    small_arr = np.asarray(small)

    def classify(r, g, b, a):
        if a < 50 or (r > 230 and g > 230 and b > 230):
            return None
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if r > 50 and g < 45 and b < 45 and lum < 70:
            return "bark"
        elif lum < 70:
            return "bark"
        elif r > 70 and g < 60 and b > 50 and lum < 100:
            return "core"
        elif lum < 170:
            return "petal_mid"
        else:
            return "petal_light"

    rects = []
    rects.append('<g class="artline" style="animation-delay:0.15s">')
    for y in range(GRID_H):
        for x in range(GRID_W):
            r, g, b, a = small_arr[y, x]
            cat = classify(r, g, b, a)
            if cat:
                fill_color = colors[cat]
                rx_pos = ART_OX + x * PIXEL_SIZE
                ry_pos = ART_OY + y * PIXEL_SIZE
                rects.append(
                    f'<rect x="{rx_pos:.1f}" y="{ry_pos:.1f}" '
                    f'width="{PIXEL_SIZE - 0.3:.1f}" height="{PIXEL_SIZE - 0.3:.1f}" '
                    f'rx="1.2" fill="{fill_color}"/>'
                )
    rects.append('</g>')
    return "\n".join(rects)


# ----------------------------------------------------------------------------
# STATS
# ----------------------------------------------------------------------------
def fetch_stats():
    stats = {"repos": "-", "stars": "-", "followers": "-"}
    try:
        headers = {"User-Agent": "profile-readme"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            f"https://api.github.com/users/{USERNAME}", headers=headers)
        user = json.load(urllib.request.urlopen(req, timeout=15))
        stats["repos"] = str(user.get("public_repos", 0))
        stats["followers"] = str(user.get("followers", 0))

        stars, page = 0, 1
        while page <= 5:
            req = urllib.request.Request(
                f"https://api.github.com/users/{USERNAME}/repos"
                f"?per_page=100&page={page}", headers=headers)
            repos = json.load(urllib.request.urlopen(req, timeout=15))
            if not repos:
                break
            stars += sum(r.get("stargazers_count", 0) for r in repos)
            page += 1
        stats["stars"] = str(stars)
    except Exception as e:
        print(f"[warn] stats fetch failed: {e}")
    return stats


# ----------------------------------------------------------------------------
# RENDER
# ----------------------------------------------------------------------------
def render(theme_name, colors, stats, ist_now):
    pixel_art_svg = render_pixel_art(colors)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, '
        f'\'JetBrains Mono\', \'Cascadia Code\', Menlo, Consolas, monospace">'
    )

    # styles + animations
    parts.append(f"""<style>
    .key  {{ fill:{colors['key']}; font-size:13px; font-weight:700; }}
    .val  {{ fill:{colors['text']}; font-size:13px; }}
    .acc  {{ fill:{colors['accent']}; font-size:13px; }}
    .wrn  {{ fill:{colors['warn']}; font-size:13px; }}
    .mut  {{ fill:{colors['muted']}; font-size:12px; }}
    .hdr  {{ fill:{colors['accent']}; font-size:15px; font-weight:700; }}
    .sec  {{ fill:{colors['muted']}; font-size:12px; letter-spacing:1px; }}
    .ttl  {{ fill:{colors['muted']}; font-size:12px; }}
    .row  {{ opacity:1; animation: fade .35s ease backwards; }}
    @keyframes fade {{ from {{ opacity:0; transform:translateY(3px); }}
                       to   {{ opacity:1; transform:translateY(0); }} }}
    .cur  {{ fill:{colors['prompt']}; animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    .artline {{ opacity:1; animation: fade .4s ease backwards; }}
    </style>""")

    # window chrome
    parts.append(
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<path d="M1 13 a12 12 0 0 1 12 -12 h{W-26} a12 12 0 0 1 12 12 v25 h{-(W-2)} z" '
        f'fill="{colors["panel"]}"/>'
    )
    parts.append(f'<line x1="1" y1="38" x2="{W-1}" y2="38" stroke="{colors["border"]}"/>')
    for i, c in enumerate(["dot1", "dot2", "dot3"]):
        parts.append(f'<circle cx="{24 + i*20}" cy="20" r="6" fill="{colors[c]}"/>')
    parts.append(
        f'<text x="{W/2}" y="24" class="ttl" text-anchor="middle">'
        f'{escape(USERNAME)} — zsh — 90×26</text>'
    )

    # command line
    parts.append(
        f'<text x="36" y="66" class="row" style="animation-delay:.05s">'
        f'<tspan class="key">➜</tspan>'
        f'<tspan class="acc" dx="8">~</tspan>'
        f'<tspan class="val" dx="8">neofetch --profile</tspan></text>'
    )

    # pixel art
    parts.append(pixel_art_svg)

    # info block
    y = INFO_Y
    delay = 0.35
    cls_map = {"val": "val", "accent": "acc", "warn": "wrn", "muted": "mut"}

    for label, value, ckey in INFO:
        d = f'style="animation-delay:{delay:.2f}s"'
        if label == "__header__":
            parts.append(f'<text x="{INFO_X}" y="{y:.1f}" class="hdr row" {d}>{escape(value)}</text>')
            y += INFO_LH
        elif label == "__rule__":
            parts.append(
                f'<line x1="{INFO_X}" y1="{y-8:.1f}" x2="{W-40}" y2="{y-8:.1f}" '
                f'stroke="{colors["border"]}" class="row" {d}/>'
            )
            y += 8
        elif label == "__blank__":
            y += 10
            continue
        elif label == "__section__":
            parts.append(f'<text x="{INFO_X}" y="{y:.1f}" class="sec row" {d}>{escape(value)}</text>')
            y += INFO_LH
        elif label == "__stats__":
            stat_txt = (f'repos {stats["repos"]}   ·   stars {stats["stars"]}'
                        f'   ·   followers {stats["followers"]}')
            parts.append(
                f'<text x="{INFO_X}" y="{y:.1f}" class="row" {d}>'
                f'<tspan class="key">⚡</tspan>'
                f'<tspan class="val" dx="8">{escape(stat_txt)}</tspan></text>'
            )
            y += INFO_LH
        else:
            cls = cls_map.get(ckey, "val")
            if label:
                parts.append(
                    f'<text x="{INFO_X}" y="{y:.1f}" class="key row" {d}>{escape(label)}</text>'
                )
            parts.append(
                f'<text x="{VAL_X}" y="{y:.1f}" class="{cls} row" {d}>{escape(value)}</text>'
            )
            y += INFO_LH
        delay += 0.07

    # footer prompt + blinking cursor
    fy = H - 24
    parts.append(
        f'<text x="36" y="{fy}" class="row" style="animation-delay:{delay+0.1:.2f}s">'
        f'<tspan class="key">➜</tspan>'
        f'<tspan class="acc" dx="8">~</tspan>'
        f'<tspan class="val" dx="8">open to ML / Computer Vision / Embedded roles</tspan>'
        f'<tspan class="cur" dx="8">█</tspan></text>'
    )
    parts.append(
        f'<text x="{W-36}" y="{fy}" class="mut" text-anchor="end">'
        f'last updated {ist_now}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    stats = fetch_stats()
    ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    stamp = ist.strftime("%d %b %Y, %H:%M IST")
    out = Path(__file__).parent
    for name, colors in THEMES.items():
        (out / f"{name}.svg").write_text(render(name, colors, stats, stamp), encoding="utf-8")
        print(f"wrote {name}.svg")


if __name__ == "__main__":
    main()
