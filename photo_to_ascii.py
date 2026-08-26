#!/usr/bin/env python3
"""
Turns a photo or pixel art image into the ASCII portrait shown on the left of the profile card.

Usage:
    python photo_to_ascii.py [path_to_image.png]
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/cherry_blossom.png"
COLS = 92
ASPECT = 1.72        # svg line-height / char-width


def convert_image(src_path: Path):
    if not src_path.exists():
        print(f"Error: file not found: {src_path}")
        sys.exit(1)

    img = Image.open(src_path).convert("RGBA")
    arr = np.asarray(img)

    # Detect white/transparent background
    is_white = (arr[:, :, 0] > 235) & (arr[:, :, 1] > 235) & (arr[:, :, 2] > 235)
    is_transparent = arr[:, :, 3] < 50
    is_bg = is_white | is_transparent
    fg_mask = ~is_bg

    ys, xs = np.nonzero(fg_mask)
    if len(xs) > 0 and len(ys) > 0:
        pad = 10
        x0 = max(0, xs.min() - pad)
        y0 = max(0, ys.min() - pad)
        x1 = min(arr.shape[1], xs.max() + pad)
        y1 = min(arr.shape[0], ys.max() + pad)
        cropped = img.crop((x0, y0, x1, y1))
    else:
        cropped = img

    cw, ch = cropped.size
    rows = max(1, int(COLS * (ch / cw) / ASPECT))

    resized = cropped.resize((COLS, rows), Image.Resampling.LANCZOS)
    arr_res = np.asarray(resized)

    lines = []
    for y in range(rows):
        line = []
        for x in range(COLS):
            r, g, b, a = arr_res[y, x]
            if a < 50 or (r > 230 and g > 230 and b > 230):
                line.append(" ")
            else:
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                if lum < 80:
                    line.append("@")
                elif lum < 110:
                    line.append("%")
                elif lum < 140:
                    line.append("#")
                elif lum < 170:
                    line.append("*")
                elif lum < 200:
                    line.append("+")
                elif lum < 225:
                    line.append("=")
                else:
                    line.append("-")
        lines.append("".join(line).rstrip())

    out_file = Path(__file__).parent / "portrait.txt"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Successfully wrote {out_file.name} ({COLS} cols x {len(lines)} rows)")


if __name__ == "__main__":
    convert_image(Path(SRC))
