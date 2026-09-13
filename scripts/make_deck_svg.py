#!/usr/bin/env python3
"""Author episode slides as 1920x1080 SVG from a bili storyboard.json.

Paper-radar's deck pipeline: storyboard -> slide SVGs -> PNG (svglib) ->
PPTX (easyslides svg_to_pptx) / video frames. Graph-positioning scenes
(topic == "图谱") embed the rendered knowledge-graph PNG full-bleed with a
title band. Typography follows the column's dark academic style.
"""
import argparse
import json
import pathlib
import re
import sys
from xml.sax.saxutils import escape

W, H = 1920, 1080
INK, DIM, PANEL, LINE, BG = "#EAF1F9", "#8FA0B3", "#141D2D", "#26324A", "#0E1420"
ACCENTS = {"hook": "#F2C14E", "context": "#7FB8E4", "method": "#9CD2B0", "evidence": "#7FB8E4",
           "limitation": "#E4907F", "closing": "#C9A6E8", "references": "#9AA5B1", "question": "#7FB8E4"}
TOPIC_ZH = {"引言": "引言", "图谱": "图谱定位", "背景": "背景", "转折": "问题", "方法": "方法",
            "算法": "算法", "证据": "证据", "局限": "局限", "启示": "启示", "参考文献": "来源"}


def esc(s):
    return escape(str(s or ""))


def wrap_chars(text, per_line):
    text = str(text or "")
    return [text[i:i + per_line] for i in range(0, len(text), per_line)] or [""]


class Slide:
    def __init__(self):
        self.p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    def text(self, x, y, s, size, fill=INK, weight="normal", anchor="start", family="Georgia, 'Songti SC', serif", spacing="0"):
        self.p.append(f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" '
                      f'font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{spacing}">{esc(s)}</text>')

    def para(self, x, y, text, size, per_line, lh, fill=INK):
        for ln in wrap_chars(text, per_line):
            self.text(x, y, ln, size, fill)
            y += lh
        return y

    def rect(self, x, y, w, h, fill=PANEL, stroke=LINE, rx=14):
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')

    def save(self, path):
        self.p.append("</svg>")
        pathlib.Path(path).write_text("\n".join(self.p), encoding="utf-8")


def kicker(sl, sc, idx, accent):
    tag = TOPIC_ZH.get(sc.get("topic"), sc.get("topic", ""))
    sl.text(120, 108, f"强化学习专栏 · 论文解读 · {tag} · {idx:02d}", 22, DIM, spacing="3")
    sl.p.append(f'<rect x="120" y="128" width="72" height="6" fill="{accent}"/>')


def cover_slide(sb, path):
    s = Slide()
    s.p.append(f'<rect width="{W}" height="{H}" fill="#0B1019"/>')
    s.p.append('<rect x="0" y="0" width="14" height="1080" fill="#4A9EBF"/>')
    s.text(W/2, 200, "PAPER RADAR · 强化学习专栏", 30, DIM, anchor="middle", spacing="6")
    en = sb.get("title_en", "")
    for i, ln in enumerate(wrap_chars(en, 44)):
        s.text(W/2, 400 + i*90, ln, 64 if i == 0 else 56, INK, "bold", "middle")
    s.text(W/2, 700, sb["title"], 44, "#BFD6E6", "normal", "middle")
    s.p.append(f'<rect x="{W/2-60}" y="760" width="120" height="4" fill="#4A9EBF"/>')
    s.text(W/2, 850, "知识图谱定位 · 全文精读 · 原创解读", 26, DIM, anchor="middle")
    s.text(W/2, 920, "mappedinfo · paper-radar", 22, "#5D6F85", anchor="middle")
    s.save(path)


def graph_slide(s, sb, png_name, title, subtitle):
    """Full-bleed graph PNG + title band."""
    png = (pathlib.Path(__file__).resolve().parents[1] / "data" / sb["slug"].replace("-", "_", 0) / "renders" / png_name)
    s.p.append(f'<image href="{png_name}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid meet"/>')
    s.p.append(f'<rect x="0" y="0" width="{W}" height="176" fill="#0B1019" opacity="0.92"/>')
    s.p.append(f'<rect x="0" y="0" width="14" height="176" fill="#4A9EBF"/>')
    s.text(120, 92, title, 52, INK, "bold")
    s.text(120, 148, subtitle, 26, DIM)


def content_slide(sl, sc, idx):
    accent = ACCENTS.get(sc["kind"], "#7FB8E4")
    kicker(sl, sc, idx, accent)
    head = sc["heading"]
    for i, ln in enumerate(wrap_chars(head, 20)):
        sl.text(120, 226 + i*74, ln, 58, INK, "bold")
    y = 320
    if sc.get("context"):
        sl.rect(120, y, 780, 0)  # placeholder no-op
    y = 340
    # context setup / implication chips
    if sc.get("context", {}).get("setup"):
        sl.rect(120, y, 800, 118, "#111A29")
        sl.text(150, y+36, "为什么是这一页", 22, accent, "bold")
        y2 = sl.para(150, y+72, sc["context"]["setup"], 24, 36, 34, "#C6D3E2")
        y = max(y + 118, y2 - 34 + 24)
    # body
    sl.text(120, y+30, "要点", 22, accent, "bold")
    y = sl.para(120, y+72, sc["body"], 30, 30, 46)
    # visual blocks
    v = sc.get("visual") or {}
    if v.get("layout") == "metrics" and v.get("items"):
        n = len(v["items"]); cw = min(400, 1560 // n)
        for i, it in enumerate(v["items"]):
            x = 120 + i * (cw + 24)
            sl.rect(x, 700, cw, 220, "#111A29")
            sl.text(x + cw/2, 788, it["value"], 52, accent, "bold", "middle")
            for j, ln in enumerate(wrap_chars(it.get("label", ""), (cw-60)//24)):
                sl.text(x + cw/2, 848 + j*32, ln, 22, DIM, anchor="middle")
    elif v.get("layout") == "limits" and v.get("items"):
        for i, it in enumerate(v["items"][:4]):
            sl.rect(120, 690 + i*74, 1560, 60, "#111A29")
            sl.p.append(f'<circle cx="160" cy="{720 + i*74}" r="8" fill="{accent}"/>')
            sl.text(200, 728 + i*74, it.split("：")[0] if "：" in it else it, 26, INK, "bold")
            if "：" in it:
                sl.text(200 + 24*len(it.split("：")[0]) + 24, 728 + i*74, it.split("：", 1)[1], 24, DIM)
    elif v.get("layout") == "closing":
        sl.rect(200, 700, 1520, 200, "#101A2A", "#3A4A61")
        sl.p.append(f'<rect x="200" y="700" width="8" height="200" fill="{accent}"/>')
        for j, ln in enumerate(wrap_chars(v.get("quote", ""), 44)):
            sl.text(W/2, 778 + j*46, ("“" + ln + "”") if j == 0 else ln, 34, INK, anchor="middle")
        sl.text(W/2, 862, "— " + v.get("source", ""), 22, DIM, anchor="middle")
    elif v.get("layout") == "references":
        y2 = 660
        for it in v.get("entries", []):
            y2 = sl.para(120, y2, it, 24, 92, 36, "#C6D3E2") + 16
    # narration as visible detailed paragraph (context contract)
    sl.p.append(f'<rect x="120" y="920" width="1680" height="4" fill="{LINE}"/>')
    sl.text(120, 956, "详细解读", 20, accent, "bold")
    sl.para(120, 988, sc["narration"], 23, 74, 32, "#AEBFD2")
    # implication line
    if sc.get("context", {}).get("implication"):
        sl.rect(960, 340, 840, 560 - 0, "#0F1826")
        sl.text(990, 396, "这一页带来什么", 22, accent, "bold")
        sl.para(990, 436, sc["context"]["implication"], 26, 30, 42, "#C6D3E2")
        sl.p.append(f'<rect x="990" y="376" width="56" height="4" fill="{accent}"/>')
    cit = sc.get("citation", "")
    if cit:
        sl.text(1800, 1044, cit, 19, "#5D6F85", anchor="end")


def build(project):
    sb = json.loads((project / "storyboard.json").read_text(encoding="utf-8"))
    out = project / "deck" / "svg"
    out.mkdir(parents=True, exist_ok=True)
    # graph renders -> copy into deck dir for embedding
    renders = pathlib.Path(__file__).resolve().parents[1] / "data" / "reinforcement-learning" / "renders"
    cover_slide(sb, out / "slide-00-cover.svg")
    for i, sc in enumerate(sb["scenes"], 1):
        s = Slide()
        if sc.get("topic") == "图谱" and i == 2:
            graph_slide(s, sb, "global.png", sc["heading"], "全局格局 · 节点=课题组 · 连线=组间引用流（自动渲染）")
        elif sc.get("topic") == "图谱":
            graph_slide(s, sb, "local.png", sc["heading"], "局部关系 · 高亮=本期论文两跳邻域（自动渲染）")
        else:
            content_slide(s, sc, i)
        s.save(out / f"slide-{i:02d}.svg")
    print(f"authored {1+len(sb['scenes'])} slide SVGs -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    build(pathlib.Path(args.project))


if __name__ == "__main__":
    sys.exit(main())
