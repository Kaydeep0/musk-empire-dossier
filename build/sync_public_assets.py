#!/usr/bin/env python3
"""Copy charts; normalize Spacexsec SVG exhibits and export PNGs for GitHub Pages."""
import os
import re
import shutil

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
PUBLIC = os.path.join(ROOT, "public")
CHARTS = os.path.join(ROOT, "charts")
SPCX_VIS = os.path.join(ROOT, "..", "Spacexsec", "build", "_visuals")

SVG_EXHIBITS = [
    "V3_three_leg_refinancing.svg",
    "V4_value_flow_loop.svg",
    "V5_lockup_calendar.svg",
]

EXHIBIT_META = {
    "V5_lockup_calendar.svg": {
        "title": "Lock-up calendar",
        "desc": "When locked insider stock can legally sell. Aug 20 roughly doubles tradable float.",
    },
    "V4_value_flow_loop.svg": {
        "title": "Value-flow loop",
        "desc": "Cash and equity routes between Tesla, SpaceX, Valor, affiliates, and public shareholders.",
    },
    "V3_three_leg_refinancing.svg": {
        "title": "Three-leg refinance",
        "desc": "Twitter LBO debt, Goldman bridge, IPO proceeds, senior notes. Bridge cliff Sep 2, 2027.",
    },
}


def normalize_svg(text):
    """Fix embed crop viewBox and em dashes for web display."""
    text = text.replace("\u2014", " - ").replace("\u2013", "-")
    text = re.sub(
        r'viewBox="0 186 1600 558"',
        'viewBox="0 0 1600 900" width="1600" height="900" preserveAspectRatio="xMidYMid meet"',
        text,
        count=1,
    )
    if 'preserveAspectRatio' not in text.split(">", 1)[0]:
        text = text.replace(
            "<svg xmlns=",
            '<svg xmlns=',
        ).replace(
            'viewBox="0 0 1600 900"',
            'viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid meet"',
            1,
        ) if 'viewBox="0 0 1600 900"' in text else text
    return text


def svg_to_png(svg_path, png_path, width=1280):
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=width)
        return True
    except Exception as e:
        print(f"png export failed {svg_path}: {e}")
        return False


def copy_tree(src_dir, rel_prefix):
    if not os.path.isdir(src_dir):
        return 0
    n = 0
    for name in os.listdir(src_dir):
        if not name.endswith(".png"):
            continue
        src = os.path.join(src_dir, name)
        rel = f"{rel_prefix}/{name}"
        dst = os.path.join(PUBLIC, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def sync_exhibits():
    out_dir = os.path.join(PUBLIC, "exhibits")
    os.makedirs(out_dir, exist_ok=True)
    synced = []
    for name in SVG_EXHIBITS:
        src = os.path.join(SPCX_VIS, name)
        if not os.path.isfile(src):
            continue
        svg_out = os.path.join(out_dir, name)
        png_name = name.replace(".svg", ".png")
        png_out = os.path.join(out_dir, png_name)
        text = normalize_svg(open(src, encoding="utf-8").read())
        open(svg_out, "w", encoding="utf-8").write(text)
        if svg_to_png(svg_out, png_out):
            synced.append({"svg": f"exhibits/{name}", "png": f"exhibits/{png_name}", "file": name})
            print(f"exhibit: {png_name}")
    return synced


def main():
    os.makedirs(os.path.join(PUBLIC, "charts"), exist_ok=True)
    n = copy_tree(CHARTS, "charts")
    print(f"copied {n} chart PNGs")
    sync_exhibits()


if __name__ == "__main__":
    main()
