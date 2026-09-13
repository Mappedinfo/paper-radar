#!/usr/bin/env python3
"""Author episode slides as 1920x1080 SVG following EasySlides design guidelines.

Design system (from easyslides/references/design-guidelines.md, scaled 1.5x to 1920x1080):
- Academic blue theme: #003366 primary / #0066CC accent / #CC0000 emphasis,
  white + #F5F7FA backgrounds, 60-30-10 rule, #D0D7E0 borders.
- Page structure: header band -> key message bar -> content area -> footer.
- storyboard context.setup / context.implication are AUTHORING aids only and
  are never rendered on slides.
"""
import argparse
import json
import pathlib
import sys
from xml.sax.saxutils import escape

W, H = 1920, 1080
INK, SUB, TER = "#333333", "#666666", "#999999"
NAVY, ACCENT, EMPH = "#003366", "#0066CC", "#CC0000"
BG2, CARD, BORDER = "#F5F7FA", "#FFFFFF", "#D0D7E0"
BLUE_L = "#E8F4FC"
FAM = "'Microsoft YaHei', '微软雅黑', Arial, sans-serif"


def esc(s):
    return escape(str(s or ""))


def wrap(text, per):
    text = str(text or "")
    return [text[i:i + per] for i in range(0, len(text), per)] or [""]


def title_size(n):
    return 54 if n <= 8 else 48 if n <= 12 else 42 if n <= 16 else 36


class Slide:
    def __init__(self, chapter, page_no):
        self.p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
                  f'<rect x="0" y="0" width="{W}" height="105" fill="{NAVY}"/>',
                  f'<rect x="60" y="41" width="10" height="34" fill="{ACCENT}"/>']
        self.text(92, 68, chapter, 30, "#FFFFFF", "bold")
        self.text(W - 60, 68, page_no, 26, "#9FB8D4", anchor="end")
        self.p.append(f'<rect x="0" y="{H-72}" width="{W}" height="72" fill="{BG2}"/>')
        self.p.append(f'<rect x="0" y="{H-72}" width="{W}" height="2" fill="{BORDER}"/>')

    def text(self, x, y, s, size, fill=INK, weight="normal", anchor="start"):
        self.p.append(f'<text x="{x}" y="{y}" fill="{fill}" font-family="{FAM}" font-size="{size}" '
                      f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')

    def para(self, x, y, text, size, per, lh, fill=INK, weight="normal"):
        for ln in wrap(text, per):
            self.text(x, y, ln, size, fill, weight)
            y += lh
        return y

    def save(self, path):
        self.p.append("</svg>")
        pathlib.Path(path).write_text("\n".join(self.p), encoding="utf-8")


def key_message(sl, heading, body):
    """Heading + key message bar (the page's one sentence)."""
    y = 190
    for ln in wrap(heading, 22):
        sl.text(90, y, ln, title_size(len(ln)), NAVY, "bold")
        y += title_size(len(ln)) + 16
    parts = body.split("。")
    lead = ""
    for s in parts[:-1]:
        lead += s + "。"
        if len(lead) >= 24:
            break
    if not lead:
        lead = body
    lead = lead[:96]
    rest = body[len(lead):]
    bar_y = y + 18
    sl.p.append(f'<rect x="90" y="{bar_y}" width="{W-180}" height="110" rx="12" fill="{BLUE_L}"/>')
    sl.p.append(f'<rect x="90" y="{bar_y}" width="10" height="110" fill="{ACCENT}"/>')
    lines = wrap(lead, 50)
    for j, ln in enumerate(lines[:2]):
        sl.text(126, bar_y + 48 + j * 44, ln, 30, NAVY, "bold")
    return rest, bar_y + 110 + 40


def content(sl, rest, sc, y):
    v = sc.get("visual") or {}
    layout = v.get("layout")
    if rest and len(rest) > 12:
        y = sl.para(90, y + 8, rest, 28, 60, 44, INK) + 26
    if layout == "metrics":
        items = v.get("items", [])
        n = max(1, len(items))
        cw = min(540, (W - 180 - 24 * (n - 1)) // n)
        ch = 250
        for i, it in enumerate(items):
            x = 90 + i * (cw + 24)
            sl.p.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="14" fill="{CARD}" stroke="{BORDER}"/>')
            sl.p.append(f'<rect x="{x}" y="{y}" width="{cw}" height="8" rx="4" fill="{ACCENT}"/>')
            sl.text(x + cw / 2, y + 128, it["value"], 58, EMPH if i == 0 else NAVY, "bold", "middle")
            for j, ln in enumerate(wrap(it.get("label", ""), (cw - 60) // 26)[:2]):
                sl.text(x + cw / 2, y + 186 + j * 34, ln, 24, SUB, anchor="middle")
        y += ch + 30
    elif layout == "limits":
        for i, it in enumerate(v.get("items", [])[:4]):
            sl.p.append(f'<rect x="90" y="{y}" width="{W-180}" height="88" rx="12" fill="{CARD}" stroke="{BORDER}"/>')
            sl.p.append(f'<circle cx="140" cy="{y+44}" r="12" fill="{EMPH}"/>')
            head, _, note = it.partition("：")
            sl.text(180, y + 38, head, 30, NAVY, "bold")
            if note:
                sl.text(180, y + 72, note, 24, SUB)
            y += 108
    elif layout == "closing":
        qy = y + 30
        sl.p.append(f'<rect x="220" y="{qy}" width="{W-440}" height="230" rx="16" fill="{NAVY}"/>')
        sl.text(W / 2, qy + 66, "“", 72, "#9FB8D4", anchor="middle")
        for j, ln in enumerate(wrap(v.get("quote", ""), 40)[:3]):
            sl.text(W / 2, qy + 120 + j * 46, ln, 32, "#FFFFFF", anchor="middle")
        sl.text(W / 2, qy + 200, "— " + v.get("source", ""), 22, "#9FB8D4", anchor="middle")
        y = qy + 260
    elif layout == "references":
        for it in v.get("entries", []):
            y = sl.para(90, y, it, 26, 88, 40, INK) + 14
    return y


def build(project):
    sb = json.loads((project / "storyboard.json").read_text(encoding="utf-8"))
    out = project / "deck" / "svg"
    out.mkdir(parents=True, exist_ok=True)

    sl = Slide("强化学习专栏 · PAPER RADAR", "封面")
    sl.p.append(f'<rect x="0" y="105" width="{W}" height="14" fill="{ACCENT}"/>')
    sl.text(W / 2, 330, "强化学习专栏 · 论文解读", 34, ACCENT, anchor="middle")
    en = sb.get("title_en", "")
    for i, ln in enumerate(wrap(en, 42)[:2]):
        sl.text(W / 2, 460 + i * 96, ln, 66 if i == 0 else 56, NAVY, "bold", "middle")
    sl.p.append(f'<rect x="{W/2-90}" y="600" width="180" height="6" fill="{ACCENT}"/>')
    for i, ln in enumerate(wrap(sb["title"], 26)[:2]):
        sl.text(W / 2, 680 + i * 60, ln, 44, INK, anchor="middle")
    sl.text(W / 2, 840, "知识图谱定位 · 全文精读 · 原创解读", 26, SUB, anchor="middle")
    sl.text(60, H - 28, "mappedinfo / paper-radar", 22, TER)
    sl.text(W - 60, H - 28, "mappedinfo.github.io/paper-radar", 22, TER, anchor="end")
    sl.save(out / "slide-00-cover.svg")

    for i, sc in enumerate(sb["scenes"], 1):
        sl = Slide("强化学习专栏 · " + (sc.get("topic") or ""), f"{i:02d} / {len(sb['scenes'])}")
        if sc.get("topic") == "图谱" and i == 2:
            sl.p.append(f'<rect x="0" y="105" width="{W}" height="{H-177}" fill="{BG2}"/>')
            sl.p.append(f'<rect x="150" y="160" width="1620" height="810" rx="12" fill="#0E1420" stroke="{BORDER}"/>')
            sl.p.append('<image href="global.png" x="165" y="175" width="1590" height="780" preserveAspectRatio="xMidYMid meet"/>')
            sl.text(180, 148, sc["heading"], 36, NAVY, "bold")
        elif sc.get("topic") == "图谱":
            sl.p.append(f'<rect x="0" y="105" width="{W}" height="{H-177}" fill="{BG2}"/>')
            sl.p.append(f'<rect x="150" y="160" width="1620" height="810" rx="12" fill="#0E1420" stroke="{BORDER}"/>')
            sl.p.append('<image href="local.png" x="165" y="175" width="1590" height="780" preserveAspectRatio="xMidYMid meet"/>')
            sl.text(180, 148, sc["heading"], 36, NAVY, "bold")
        else:
            rest, y = key_message(sl, sc["heading"], sc["body"])
            y = content(sl, rest, sc, y)
            if sc["kind"] not in ("references",):
                ny = min(y + 6, 740)
                sl.p.append(f'<rect x="90" y="{ny}" width="{W-180}" height="{880-ny}" rx="12" fill="{BG2}"/>')
                sl.text(120, ny + 40, "详细解读", 24, ACCENT, "bold")
                sl.para(120, ny + 80, sc["narration"], 25, 78, 36, SUB)
        cit = sc.get("citation", "")
        if cit:
            sl.text(60, H - 28, cit, 22, TER)
        sl.text(W - 60, H - 28, "强化学习专栏 · paper-radar", 22, TER, anchor="end")
        sl.save(out / f"slide-{i:02d}.svg")
    print(f"authored {1+len(sb['scenes'])} EasySlides-style slide SVGs -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    build(pathlib.Path(args.project))


if __name__ == "__main__":
    sys.exit(main())
