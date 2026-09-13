#!/usr/bin/env python3
"""Author academic episode slides (1920x1080 SVG) — design v3.

v3 principles (episode-deck-blueprint.md):
- Academic running header: paper short-title (left) + source section origin
  (right, from scene.citation), plus a chapter progress ribbon.
- Full-sentence thesis + complete body text; numbered figures/tables/equations
  with captions (图 N / 表 N / 式 N), never marketing cards.
- Narration is NEVER rendered; it goes to PPTX speaker notes (build_pptx.py).
- One font family; fixed type ramp; two weights only.
- Cursor-based layout with line counting; auto step-down on overflow; no
  overlapping elements.
"""
import argparse
import json
import pathlib
import sys
from xml.sax.saxutils import escape

W, H = 1920, 1080
NAVY, ACCENT = "#003366", "#0066CC"
INK, SUB, TER = "#333333", "#666666", "#999999"
BG2, BORDER = "#F5F7FA", "#D0D7E0"
FAM = "'Microsoft YaHei', '微软雅黑', Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"
CHAPTERS = ["引言", "图谱", "背景", "方法", "实验", "局限", "启示", "来源"]
TOPIC2CH = {"引言": "引言", "图谱": "图谱", "背景": "背景", "问题": "背景", "转折": "背景",
            "方法": "方法", "算法": "方法", "训练": "方法", "证据": "实验", "结果": "实验",
            "涌现": "实验", "局限": "局限", "边界": "局限", "启示": "启示", "参考文献": "来源"}


def esc(s):
    return escape(str(s or ""))


def wrap(text, per):
    text = str(text or "")
    return [text[i:i + per] for i in range(0, len(text), per)] or [""]


class Page:
    """Cursor-based page builder. All y positions derive from measured lines."""

    def __init__(self, paper_tag, section_origin, chapter):
        self.p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
        # running header (h=72): paper tag left, section origin right
        self.p.append(f'<rect x="0" y="0" width="{W}" height="72" fill="#FFFFFF"/>')
        self.p.append(f'<rect x="0" y="70" width="{W}" height="2" fill="{BORDER}"/>')
        self.p.append(f'<rect x="72" y="26" width="8" height="28" fill="{NAVY}"/>')
        self.text(96, 48, paper_tag, 22, SUB)
        if section_origin:
            self.text(W - 72, 48, section_origin, 22, ACCENT, "bold", "end")
        # chapter ribbon (y=72..120)
        self.p.append(f'<rect x="0" y="72" width="{W}" height="48" fill="{BG2}"/>')
        seg_w = (W - 144) / len(CHAPTERS)
        for i, ch in enumerate(CHAPTERS):
            x = 72 + i * seg_w
            active = (ch == chapter)
            if active:
                self.p.append(f'<rect x="{x+4}" y="80" width="{seg_w-8}" height="32" rx="6" fill="{NAVY}"/>')
            self.text(x + seg_w / 2, 102, ch, 19, "#FFFFFF" if active else TER, "bold" if active else "normal", "middle")
        self.y = 168  # content cursor
        self.footer(section_origin)

    def footer(self, src):
        self.p.append(f'<rect x="0" y="{H-58}" width="{W}" height="58" fill="#FFFFFF"/>')
        self.p.append(f'<rect x="0" y="{H-58}" width="{W}" height="2" fill="{BORDER}"/>')
        self.text(72, H - 22, src or "", 18, TER)
        self.text(W - 72, H - 22, "强化学习专栏 · Paper Radar", 18, TER, anchor="end")

    def text(self, x, y, s, size, fill=INK, weight="normal", anchor="start", family=FAM):
        self.p.append(f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" '
                      f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')

    def title(self, heading, size=40):
        lines = wrap(heading, 24)[:2]
        for ln in lines:
            self.text(72, self.y, ln, size, NAVY, "bold")
            self.y += size + 18
        self.p.append(f'<rect x="72" y="{self.y-8}" width="88" height="5" fill="{ACCENT}"/>')
        self.y += 34

    def thesis(self, claim):
        lines = wrap(claim, 54)[:2]
        h = 34 + len(lines) * 42
        self.p.append(f'<rect x="72" y="{self.y}" width="{W-144}" height="{h}" rx="8" fill="{BG2}"/>')
        self.p.append(f'<rect x="72" y="{self.y}" width="8" height="{h}" fill="{NAVY}"/>')
        for j, ln in enumerate(lines):
            self.text(108, self.y + 38 + j * 42, ln, 27, NAVY, "bold")
        self.y += h + 30

    def body(self, text, size=24, per=62, lh=38, fill=INK):
        lines = wrap(text, per)
        while self.y + len(lines) * lh > H - 90 and size > 20:
            size -= 2
            lh -= 3
            per = int(per * size / 24)
            lines = wrap(text, per)
        for ln in lines:
            self.text(72, self.y, ln, size, fill)
            self.y += lh
        self.y += 18

    def equation(self, eq, tag):
        self.p.append(f'<rect x="180" y="{self.y}" width="{W-360}" height="108" rx="8" fill="#FFFFFF" stroke="{BORDER}"/>')
        self.text(W / 2 - 60, self.y + 62, eq, 26, INK, "normal", "middle", SERIF)
        self.text(W - 210, self.y + 92, f"（{tag}）", 20, SUB, anchor="end")
        self.y += 128

    def table(self, caption, items, tag):
        rows = len(items) + 1
        col1, col2 = 640, W - 144 - 640
        rh = 64
        th = rh * rows
        cap_y = self.y
        self.text(72, cap_y + 26, f"表 {tag} ｜ {caption}", 20, SUB)
        ty = cap_y + 44
        self.p.append(f'<rect x="72" y="{ty}" width="{W-144}" height="{rh}" fill="{NAVY}"/>')
        self.text(120, ty + 40, "指标", 22, "#FFFFFF", "bold")
        self.text(72 + col1 + 40, ty + 40, "含义与条件", 22, "#FFFFFF", "bold")
        for i, it in enumerate(items, 1):
            yy = ty + i * rh
            fill = "#FFFFFF" if i % 2 else BG2
            self.p.append(f'<rect x="72" y="{yy}" width="{W-144}" height="{rh}" fill="{fill}" stroke="{BORDER}"/>')
            self.text(120, yy + 40, str(it["value"]), 26, NAVY, "bold")
            lbl = wrap(it.get("label", ""), (col2 - 80) // 22)
            if lbl:
                self.text(72 + col1 + 40, yy + 40, lbl[0], 22, INK)
        self.y = ty + th + 26

    def figure(self, href, caption, tag):
        cap_y = self.y
        self.text(72, cap_y + 24, f"图 {tag} ｜ {caption}", 20, SUB)
        img_h = min(H - 120 - (cap_y + 44), 700)
        img_w = int(img_h * 16 / 9) if False else W - 144
        ih = img_h
        iw = min(int(ih * 1.78), W - 144)
        ih2 = int(iw / 1.78)
        x = (W - iw) / 2
        self.p.append(f'<rect x="{x-2}" y="{cap_y+40}" width="{iw+4}" height="{ih2+4}" fill="#0E1420" stroke="{BORDER}"/>')
        self.p.append(f'<image href="{href}" x="{x}" y="{cap_y+42}" width="{iw}" height="{ih2}" preserveAspectRatio="xMidYMid meet"/>')
        self.y = cap_y + 44 + ih2 + 26

    def limits(self, items, tag):
        self.text(72, self.y + 4, f"表 {tag} ｜ 局限与边界", 20, SUB)
        self.y += 28
        for i, it in enumerate(items[:4], 1):
            head, _, note = it.partition("：")
            h = 66
            self.p.append(f'<rect x="72" y="{self.y}" width="{W-144}" height="{h}" fill="{BG2 if i%2==0 else "#FFFFFF"}" stroke="{BORDER}"/>')
            self.text(104, self.y + 40, f"{i}.", 22, NAVY, "bold")
            self.text(150, self.y + 40, head, 24, NAVY, "bold")
            if note:
                self.text(150 + len(head) * 24 + 30, self.y + 40, note, 22, SUB)
            self.y += h
        self.y += 22

    def quote(self, text_, source):
        self.p.append(f'<rect x="150" y="{self.y}" width="{W-300}" height="200" rx="10" fill="{BG2}"/>')
        self.text(W / 2, self.y + 74, "“", 64, ACCENT, "bold", "middle", SERIF)
        for j, ln in enumerate(wrap(text_, 38)[:2]):
            self.text(W / 2, self.y + 118 + j * 44, ln, 28, NAVY, anchor="middle")
        self.text(W / 2, self.y + 172, "— " + source, 20, SUB, anchor="middle")
        self.y += 224

    def save(self, path):
        if self.y > H - 70:
            print(f"  WARN overflow on {path.name}: cursor {self.y:.0f}")
        self.p.append("</svg>")
        pathlib.Path(path).write_text("\n".join(self.p), encoding="utf-8")


def sect_origin(cit):
    """'Lucas & Precup, 2026 · §3.1–§3.2' -> '§3.1–§3.2 · Lucas & Precup 2026'."""
    if not cit or "图谱" in cit:
        return ""
    parts = cit.split("·")
    if len(parts) >= 2:
        return f"{parts[1].strip()} · {parts[0].strip()}"
    return cit


def build(project):
    sb = json.loads((project / "storyboard.json").read_text(encoding="utf-8"))
    out = project / "deck" / "svg"
    out.mkdir(parents=True, exist_ok=True)
    tag = sb["title_en"][:46]
    n = len(sb["scenes"])

    # cover: paper title page
    pg = Page("强化学习专栏 · Paper Radar", "", "引言")
    pg.p.append(f'<rect x="0" y="120" width="{W}" height="3" fill="{NAVY}"/>')
    pg.text(72, 220, "论文解读 · Paper Radar 专栏", 24, ACCENT, "bold")
    en_lines = wrap(sb.get("title_en", ""), 40)[:2]
    for i, ln in enumerate(en_lines):
        pg.text(72, 330 + i * 84, ln, 58 if i == 0 else 48, NAVY, "bold")
    rule_y = 330 + len(en_lines) * 84 + 10
    pg.p.append(f'<rect x="72" y="{rule_y}" width="120" height="5" fill="{ACCENT}"/>')
    for i, ln in enumerate(wrap(sb["title"], 30)[:2]):
        pg.text(72, 560 + i * 56, ln, 40, INK)
    pg.text(72, 700, sb.get("publish", {}).get("description", "")[:78] + "…", 22, SUB)
    pg.text(72, 760, "关键词 ｜ " + "、".join(sb.get("publish", {}).get("tags", [])), 22, SUB)
    pg.p.append(f'<rect x="72" y="820" width="720" height="96" rx="8" fill="{BG2}"/>')
    pg.text(104, 858, "结构 ｜ 全局图谱 → 局部定位 → 背景 → 方法 → 实验 → 局限 → 启示", 22, NAVY)
    pg.text(104, 892, "讲解音轨见备注页", 20, TER)
    pg.save(out / "slide-00-cover.svg")

    fig_n = 0
    tab_n = 0
    eq_n = 0
    for i, sc in enumerate(sb["scenes"], 1):
        chapter = TOPIC2CH.get(sc.get("topic"), "方法")
        origin = sect_origin(sc.get("citation", ""))
        pg = Page(tag, origin, chapter)
        pg.title(sc["heading"])
        body = sc["body"]
        v = sc.get("visual") or {}
        lay = v.get("layout")
        # thesis = first sentence(s) up to >=24 chars
        parts = body.split("。")
        claim = ""
        for s in parts[:-1]:
            claim += s + "。"
            if len(claim) >= 24:
                break
        claim = claim if claim else body
        rest = body[len(claim):].lstrip()
        if sc.get("topic") == "图谱" and i == 2:
            fig_n += 1
            pg.figure("global.png", "强化学习领域全局格局（节点为课题组，尺寸为实力分，连线为组间引用流；数据 OpenAlex/arXiv，2026-09-13）", fig_n)
        elif sc.get("topic") == "图谱":
            fig_n += 1
            pg.figure("local.png", "本期论文的局部引用网络（发光节点为焦点，两跳邻域，虚线为成员关系）", fig_n)
        else:
            if sc["kind"] not in ("references",):
                pg.thesis(claim)
            if rest:
                pg.body(rest)
            if sc.get("equation"):
                eq_n += 1
                pg.equation(sc["equation"][0], f"式 {eq_n}")
                if len(sc["equation"]) > 1 and sc["equation"][1]:
                    pg.body(sc["equation"][1], size=22, per=66, lh=34, fill=SUB)
            if lay == "metrics":
                tab_n += 1
                pg.table(v.get("table_caption", "关键指标"), v.get("items", []), tab_n)
            elif lay == "limits":
                tab_n += 1
                pg.limits(v.get("items", []), tab_n)
            elif lay == "closing":
                pg.quote(v.get("quote", ""), v.get("source", ""))
            elif lay == "references":
                for it in v.get("entries", []):
                    pg.body(it, size=24, per=76, lh=40)
        pg.save(out / f"slide-{i:02d}.svg")
    print(f"authored {1+n} academic slides (v3) -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    build(pathlib.Path(args.project))


if __name__ == "__main__":
    sys.exit(main())
