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

# Tight crops per diagram (original PDF embed used 0 186 1600 558; full 900px canvas adds whitespace).
EXHIBIT_VIEWBOX = {
    "V3_three_leg_refinancing.svg": "80 300 1440 240",
    "V4_value_flow_loop.svg": "60 230 1480 610",
    "V5_lockup_calendar.svg": "60 230 1480 510",
}


def patch_exhibit(name, text):
    """Web-safe dashes, layout fixes, and tight viewBox for each exhibit."""
    text = (
        text.replace("\u2014", " - ")
        .replace("\u2013", "-")
        .replace("\u2012", "-")
        .replace("–", "-")
        .replace("—", " - ")
    )

    if name == "V4_value_flow_loop.svg":
        # Footer sat on top of bottom entity boxes; arrow labels overlapped center hub.
        text = re.sub(
            r'(<text x="800" y=")670(" font-family="Helvetica, Arial, sans-serif" font-size="24.0" fill="#1A1A1A" font-weight="bold" text-anchor="middle" letter-spacing="0">Recurring intra-empire)',
            r'\g<1>805\2',
            text,
        )
        text = re.sub(
            r'(<text x="520" y=")650(" font-family="Helvetica, Arial, sans-serif" font-size="19.5" fill="#C0392B")',
            r'\g<1>592\2',
            text,
        )
        text = re.sub(
            r'(<text x="1090" y=")650(" font-family="Helvetica, Arial, sans-serif" font-size="19.5" fill="#5A5A5A")',
            r'\g<1>592\2',
            text,
        )
        text = re.sub(
            r'(<text x="1080" y=")360(" font-family="Helvetica, Arial, sans-serif" font-size="19.5" fill="#1B7A4B")',
            r'\g<1>248\2',
            text,
        )
        text = re.sub(
            r'(<text x="520" y=")360(" font-family="Helvetica, Arial, sans-serif" font-size="19.5" fill="#B8860B")',
            r'\g<1>348\2',
            text,
        )

    vb = EXHIBIT_VIEWBOX.get(name, "0 186 1600 558")
    text = re.sub(
        r'<svg xmlns="http://www.w3.org/2000/svg" viewBox="[^"]*"',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="1600" height="900" preserveAspectRatio="xMidYMid meet"',
        text,
        count=1,
    )
    return text


def svg_to_png(svg_path, png_path, width=1600):
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
        text = patch_exhibit(name, open(src, encoding="utf-8").read())
        open(svg_out, "w", encoding="utf-8").write(text)
        if svg_to_png(svg_out, png_out):
            synced.append({"svg": f"exhibits/{name}", "png": f"exhibits/{png_name}", "file": name})
            print(f"exhibit: {name} + {png_name}")
    return synced


def main():
    os.makedirs(os.path.join(PUBLIC, "charts"), exist_ok=True)
    n = copy_tree(CHARTS, "charts")
    print(f"copied {n} chart PNGs")
    sync_exhibits()


if __name__ == "__main__":
    main()
