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


def convert(chrome, svg, out):
    url = svg.resolve().as_uri() + "?x=" + str(svg.stat().st_size)
    out = out.with_suffix(".png")
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--screenshot={out}", "--window-size=1920,1080",
                    "--hide-scrollbars", "--force-device-scale-factor=1", url],
                   check=True, capture_output=True, timeout=120)
    if not out.exists() or out.stat().st_size < 5000:
        raise SystemExit(f"screenshot failed for {svg}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svgs", nargs="+")
    ap.add_argument("--out-dir")
    args = ap.parse_args()
    chrome = find_chrome()
    outs = []
    for pat in args.svgs:
        for svg in map(pathlib.Path, glob.glob(pat)):
            out = pathlib.Path(args.out_dir) / svg.stem if args.out_dir else svg.parent
            if args.out_dir:
                out.mkdir(parents=True, exist_ok=True)
            outs.append(convert(chrome, svg, out / svg.stem))
            print(f"{svg.name} -> {outs[-1].name} ({outs[-1].stat().st_size//1024} KB)")
    print(f"{len(outs)} PNGs rendered")


if __name__ == "__main__":
    sys.exit(main())
