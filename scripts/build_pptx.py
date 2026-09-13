#!/usr/bin/env python3
"""Assemble the episode PPTX: slide PNGs full-bleed + narration as speaker notes.

Usage: python build_pptx.py <project_dir>
Output: deck/<slug>-deck.pptx (16:9). Notes text = scene.narration; cover notes
carry the episode intro. Run make_deck_svg.py + svg2png.py first.
"""
import argparse
import json
import pathlib
import sys

from pptx import Presentation
from pptx.util import Inches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    p = pathlib.Path(args.project).resolve()
    sb = json.loads((p / "storyboard.json").read_text(encoding="utf-8"))
    pngs = sorted((p / "deck" / "svg").glob("slide-*.png"))
    if not pngs:
        sys.exit("no slide PNGs; run make_deck_svg.py + svg2png.py first")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    scenes = sb["scenes"]
    notes = ["栏目说明：" + sb["title"] + "。" + sb.get("subtitle", "")] + \
            [sc.get("narration", "") for sc in scenes]
    for k, png in enumerate(pngs):
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(str(png), 0, 0, width=prs.slide_width, height=prs.slide_height)
        note = notes[k] if k < len(notes) else ""
        slide.notes_slide.notes_text_frame.text = note
    out = p / "deck" / f"{sb['slug']}-deck.pptx"
    prs.save(str(out))
    print(f"{out} ({len(pngs)} slides, notes on every slide)")


if __name__ == "__main__":
    sys.exit(main())
