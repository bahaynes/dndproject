#!/usr/bin/env python3
"""Generate West Marches brand icons as hand-built SVG geometry.

A face-on d20 (half an icosahedron: hexagon + 10 triangular faces) inside a
compass bezel whose west point is elongated -- "dice + heading west".

SVGs are pure stdlib. PNG/ICO rasterising needs resvg-py + pillow:
    uv run --no-project --with resvg-py --with pillow scripts/brand/gen_icons.py frontend/static/brand
"""
import math
import sys
from pathlib import Path

# Palette from frontend/src/app.css ("tabletop" theme)
BG = "#111318"        # base-100
BG_RING = "#1F242D"   # base-300
INK = "#14120E"       # primary-content (facet lines)
GOLD_HI = "#E9C778"   # lit face (lighter primary)
GOLD = "#D4A853"      # primary
BRONZE = "#C58F46"    # accent
BRONZE_LO = "#8A6230" # shadowed faces
BRONZE_DK = "#5E4222"


def pt(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def poly(points, fill, extra=""):
    d = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{d}" fill="{fill}"{extra}/>'


def d20(cx, cy, R, stroke_w):
    """Face-on icosahedron. Hex vertices V0..V5 clockwise from top."""
    V = [pt(cx, cy, R, -90 + 60 * i) for i in range(6)]
    r = R * 0.56
    A = pt(cx, cy, r, -90)   # under V0
    B = pt(cx, cy, r, 30)    # toward V2
    C = pt(cx, cy, r, 150)   # toward V4
    # Light from upper-left.
    faces = [
        ((V[0], A, V[5]), GOLD),        # upper-left
        ((V[0], V[1], A), BRONZE),      # upper-right
        ((V[5], C, A), GOLD),           # left (adjacent to centre)
        ((V[4], V[5], C), BRONZE),      # lower-left outer
        ((V[1], A, B), BRONZE),         # right (adjacent to centre)
        ((V[1], V[2], B), BRONZE_LO),   # right outer
        ((V[2], V[3], B), BRONZE_DK),   # lower-right outer
        ((V[3], C, B), BRONZE_LO),      # bottom (adjacent to centre)
        ((V[3], V[4], C), BRONZE_LO),   # lower-left outer
        ((A, B, C), GOLD_HI),           # front face
    ]
    line = (f' stroke="{INK}" stroke-width="{stroke_w:.2f}" '
            f'stroke-linejoin="round"')
    return "\n".join(poly(p, f, line) for p, f in faces)


def compass(cx, cy, r_ring, ring_w):
    """Bezel ring with cardinal spikes; west spike is the long one."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r_ring:.2f}" fill="none" '
           f'stroke="{GOLD}" stroke-width="{ring_w:.2f}"/>']
    for deg, length, half in ((-90, 0.13, 7), (0, 0.13, 7), (90, 0.13, 7),
                              (180, 0.30, 9)):
        tip = pt(cx, cy, r_ring * (1 + length), deg)
        base_in = r_ring * 0.92
        l = pt(cx, cy, base_in, deg - half)
        rr = pt(cx, cy, base_in, deg + half)
        out.append(poly((l, tip, rr), GOLD if deg != 180 else GOLD_HI,
                        f' stroke="{BG}" stroke-width="{ring_w*0.5:.2f}"'
                        ' stroke-linejoin="round"'))
    # minor ticks on the diagonals
    for deg in (-45, 45, 135, 225):
        a = pt(cx, cy, r_ring * 1.0, deg)
        b = pt(cx, cy, r_ring * 1.08, deg)
        out.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" '
                   f'y2="{b[1]:.2f}" stroke="{GOLD}" '
                   f'stroke-width="{ring_w:.2f}" stroke-linecap="round"/>')
    return "\n".join(out)


def svg(body, size=512):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
            f'height="{size}" viewBox="0 0 512 512">\n'
            f'<title>West Marches</title>\n{body}\n</svg>\n')


def full_icon(shape="rounded"):
    """Detailed mark: bezel + d20. shape: rounded | square | circle."""
    if shape == "rounded":
        bg = f'<rect width="512" height="512" rx="112" fill="{BG}"/>'
    elif shape == "circle":
        bg = f'<circle cx="256" cy="256" r="256" fill="{BG}"/>'
    else:  # full-bleed square: Discord / maskable crop it themselves
        bg = f'<rect width="512" height="512" fill="{BG}"/>'
    # Shift right a touch so the long west spike balances optically.
    cx, cy = 270, 256
    glow = (f'<circle cx="{cx}" cy="{cy}" r="172" fill="{BG_RING}"/>')
    return svg("\n".join([bg, glow, compass(cx, cy, 190, 11),
                          d20(cx, cy, 148, 7)]))


def small_icon(stroke=16):
    """Favicon: no bezel (it turns to mush at 16px), die fills the tile."""
    bg = f'<rect width="512" height="512" rx="96" fill="{BG}"/>'
    return svg("\n".join([bg, d20(256, 260, 220, stroke)]))


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "icon.svg": full_icon("rounded"),
        "icon-square.svg": full_icon("square"),
        "favicon.svg": small_icon(),
        "favicon-tiny.svg": small_icon(stroke=30),
    }
    for name, text in files.items():
        (out / name).write_text(text)

    try:
        import io
        import resvg_py
        from PIL import Image
    except ImportError:
        print("SVGs written; install resvg-py + pillow for PNG/ICO")
        return

    def render(svg_text, px):
        png = resvg_py.svg_to_bytes(svg_string=svg_text, width=px, height=px)
        return Image.open(io.BytesIO(bytes(png))).convert("RGBA")

    render(files["icon-square.svg"], 1024).save(out / "discord-1024.png")
    render(files["icon-square.svg"], 512).save(out / "icon-512.png")
    render(files["icon-square.svg"], 192).save(out / "icon-192.png")
    render(files["icon-square.svg"], 180).save(out / "apple-touch-icon.png")
    # ICO: favicon art at small sizes, rendered per-size rather than downscaled
    ico = [render(files["favicon-tiny.svg"], 16),
           render(files["favicon.svg"], 32), render(files["favicon.svg"], 48)]
    ico[-1].save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
                 append_images=ico[:-1])
    render(files["favicon-tiny.svg"], 16).save(out / "favicon-16.png")
    for s in (32, 64):
        render(files["favicon.svg"], s).save(out / f"favicon-{s}.png")
    print(f"wrote {len(list(out.iterdir()))} files to {out}")


if __name__ == "__main__":
    main()
