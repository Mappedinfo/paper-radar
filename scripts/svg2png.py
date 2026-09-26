#!/usr/bin/env python3
"""Rasterize 1920x1080 SVGs to PNG with playwright's chrome-headless-shell.

Usage: python svg2png.py <in.svg> [<in2.svg> ...] [--out-dir DIR]
Output: <stem>.png next to input (or in --out-dir).
"""
import argparse
import glob
import pathlib
import subprocess
import sys

CANDIDATES = [
    r"C:\Users\Admin\AppData\Local\ms-playwright\chromium_headless_shell-*\chrome-headless-shell-win64\chrome-headless-shell.exe",
]


def find_chrome():
    for pat in CANDIDATES:
        hits = glob.glob(pat)
        if hits:
            return sorted(hits)[-1]
    raise SystemExit("chrome-headless-shell not found under ms-playwright")


def convert(chrome, svg, out, bg=None):
    url = svg.resolve().as_uri() + "?x=" + str(svg.stat().st_size)
    # stem may itself contain dots (arxiv ids); with_suffix would eat them
    out = out.parent / (out.name + ".png") if not out.name.endswith(".png") else out
    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox",
           f"--screenshot={out}", "--window-size=1920,1080",
           "--hide-scrollbars", "--force-device-scale-factor=1"]
    if bg:
        # page background behind transparent SVGs, e.g. FFFFFFFF for white
        cmd.append(f"--default-background-color={bg}")
    cmd.append(url)
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    if not out.exists() or out.stat().st_size < 5000:
        raise SystemExit(f"screenshot failed for {svg}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svgs", nargs="+")
    ap.add_argument("--out-dir")
    ap.add_argument("--bg", help="8-digit hex page background under transparent SVGs, e.g. FFFFFFFF")
    args = ap.parse_args()
    chrome = find_chrome()
    outs = []
    for pat in args.svgs:
        for svg in map(pathlib.Path, glob.glob(pat)):
            out = pathlib.Path(args.out_dir) / svg.stem if args.out_dir else svg.parent
            if args.out_dir:
                out.mkdir(parents=True, exist_ok=True)
            outs.append(convert(chrome, svg, out / svg.stem, args.bg))
            print(f"{svg.name} -> {outs[-1].name} ({outs[-1].stat().st_size//1024} KB)")
    print(f"{len(outs)} PNGs rendered")


if __name__ == "__main__":
    sys.exit(main())
