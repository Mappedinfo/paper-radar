#!/usr/bin/env python3
"""Export every slide of a project's deck PPTX to 1920x1080 PNG (video frames).

Usage: python export_pptx_png.py <project_dir>
Output: deck/svg/slide-NN.png (00 = cover)
"""
import os
import pathlib
import sys

import win32com.client


def main():
    p = pathlib.Path(sys.argv[1]).resolve()
    src = p / "deck" / f"{p.name}-deck.pptx"
    outdir = p / "deck" / "svg"
    outdir.mkdir(parents=True, exist_ok=True)
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(src), WithWindow=False)
    for i, slide in enumerate(pres.Slides, 0):
        slide.Export(os.path.join(outdir, f"slide-{i:02d}.png"), "PNG", 1920, 1080)
    pres.Close()
    app.Quit()
    print(f"exported {len(list(outdir.glob('slide-*.png')))} PNGs -> {outdir}")


if __name__ == "__main__":
    sys.exit(main())
