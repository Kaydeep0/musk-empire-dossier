#!/usr/bin/env python3
"""Copy charts and Spacexsec SVG exhibits into public/."""
import os
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
    "V8_premium_stack.svg",
]


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


def main():
    os.makedirs(os.path.join(PUBLIC, "charts"), exist_ok=True)
    os.makedirs(os.path.join(PUBLIC, "exhibits"), exist_ok=True)
    n = copy_tree(CHARTS, "charts")
    print(f"copied {n} chart PNGs")
    m = 0
    for name in SVG_EXHIBITS:
        src = os.path.join(SPCX_VIS, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(PUBLIC, "exhibits", name))
            m += 1
    print(f"copied {m} Spacexsec SVG exhibits")


if __name__ == "__main__":
    main()
