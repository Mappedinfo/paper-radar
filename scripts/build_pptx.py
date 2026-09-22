#!/usr/bin/env python3
"""Build the EDITABLE episode PPTX — design v4 (huashu-slides informed).

Key changes from v3.2 (informed by huashu-slides + design-principles):
- ASSERTION TITLES: scene.heading renders as a full assertion sentence
  (larger, 2-line wrap allowed). Topic word + section label become a small
  kicker ABOVE the title, per assertion-evidence framework.
- TYPE HIERARCHY 3:1 — title 40pt, kicker 13pt, body 14pt. Typography is a
  design element, not an information container.
- ONE IDEA PER SLIDE — body copy ≤ 4 lines; the rest goes to speaker notes
  (narration). No long paragraphs on slides.
- HERO NUMBER — evidence slides lead with the paper's key number at 60pt+
  as a visual anchor (Fathom data narrative style).
- 60-30-10 with generous whitespace: light bg 60%, ink 30%, accent 10%.
- Full-bleed edge bar (left accent spine) + running header/footer retained.
- Overlap audit gate retained (v3.2).
"""
import argparse
import json
import pathlib
import re
import sys
from functools import lru_cache

from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

EMU_W, EMU_H = Inches(13.333), Inches(7.5)
FOOTER_TOP = Inches(7.02)
NAVY, ACCENT = RGBColor(0x00, 0x33, 0x66), RGBColor(0xD4, 0x48, 0x0B)  # Pentagram orange-red
INK, SUB, TER = RGBColor(0x1A, 0x1A, 0x1A), RGBColor(0x66, 0x66, 0x66), RGBColor(0x99, 0x99, 0x99)
BG2, BORDER, WHITE = RGBColor(0xFF, 0xFD, 0xF7), RGBColor(0xD0, 0xD7, 0xE0), RGBColor(0xFF, 0xFF, 0xFF)
CREAM = RGBColor(0xFF, 0xFD, 0xF7)
FAM = "Microsoft YaHei"
SERIF = "Georgia"
FONTS = {"regular": r"C:\Windows\Fonts\msyh.ttc", "bold": r"C:\Windows\Fonts\msyhbd.ttc"}
CHAPTERS = ["引言", "图谱", "背景", "方法", "实验", "局限", "启示", "来源"]
CHAPTER_EN = ["INTRO", "GRAPH", "CONTEXT", "METHOD", "RESULTS", "LIMITS", "TAKEAWAY", "REFS"]
TOPIC2CH = {"引言": "引言", "图谱": "图谱", "背景": "背景", "问题": "背景", "转折": "背景",
            "方法": "方法", "算法": "方法", "训练": "方法", "证据": "实验", "结果": "实验",
            "局限": "局限", "边界": "局限", "启示": "启示", "参考文献": "来源"}
PX_PER_IN = 96


@lru_cache(maxsize=256)
def _font(pt, bold):
    return ImageFont.truetype(FONTS["bold" if bold else "regular"], int(round(pt * PX_PER_IN / 72)))


# SAFETY < 1.0: PIL and PowerPoint metrics differ slightly; measure conservatively
# so PowerPoint never re-wraps a line we already fit (which produced orphan breaks).
SAFETY = 0.97
_ASCII_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'.+/&_-]*")


def _tokens(paragraph):
    """Latin words stay whole tokens; every CJK char is its own token; spaces pass through."""
    toks = []
    i = 0
    while i < len(paragraph):
        m = _ASCII_WORD.match(paragraph, i)
        if m:
            toks.append(m.group(0))
            i = m.end()
        else:
            toks.append(paragraph[i])
            i += 1
    return toks


def measure_lines(text, pt, width_in, bold=False):
    f = _font(pt, bold)
    max_px = width_in * PX_PER_IN * SAFETY
    out = []
    for para in str(text).split("\n"):
        if not para:
            out.append("")
            continue
        cur = ""
        for tok in _tokens(para):
            if tok == " " and not cur:
                continue
            trial = cur + tok
            if f.getlength(trial) <= max_px or not cur:
                cur = trial
            else:
                out.append(cur.rstrip())
                cur = tok.lstrip() if tok == " " else tok
        out.append(cur.rstrip())
    return [ln for ln in out]


def text_h(lines, pt, leading=1.32):
    return int(Inches(len(lines) * (pt * leading) / 72 + 0.10))


class Audit:
    def __init__(self):
        self.violations = []

    def check(self, slide_no, shapes, footer_top=FOOTER_TOP):
        boxes = [s for s in shapes if s["kind"] not in ("band", "bar", "line", "frame")]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                ox = min(a["l"] + a["w"], b["l"] + b["w"]) - max(a["l"], b["l"])
                oy = min(a["t"] + a["h"], b["t"] + b["h"]) - max(a["t"], b["t"])
                if ox > 27432 and oy > 27432:
                    self.violations.append(
                        f"slide {slide_no}: OVERLAP {a['name']} x {b['name']} "
                        f"({ox/914400:.2f}x{oy/914400:.2f} in)")
        for s in boxes:
            if s["t"] + s["h"] > footer_top + 9144:
                self.violations.append(
                    f"slide {slide_no}: {s['name']} crosses footer "
                    f"(bottom {(s['t']+s['h'])/914400:.2f}in)")


class PS:
    """Page builder — Pentagram editorial layout with accent spine."""

    def __init__(self, prs, paper_tag, origin, chapter_idx, footer_left):
        self.s = prs.slides.add_slide(prs.slide_layouts[6])
        self.shapes_audit = []
        self.y = Inches(0.55)
        # left accent spine (full height, 0.14in)
        self.rect(0, 0, Inches(0.14), EMU_H, fill=NAVY, line=None, kind="bar")
        # running header: EN section label left / paper tag right
        self.text(Inches(0.55), Inches(0.28), Inches(5.0), CHAPTER_EN[chapter_idx], Pt(13), ACCENT, True,
                  name="hdr-left", kind="band")
        self.text(Inches(6.0), Inches(0.28), Inches(6.8), paper_tag, Pt(13), SUB,
                  align=PP_ALIGN.RIGHT, name="hdr-right", kind="bar")
        # hairline under header
        ln = self.s.shapes.add_connector(1, int(Inches(0.55)), int(Inches(0.62)), int(EMU_W - Inches(0.55)), int(Inches(0.62)))
        ln.line.color.rgb = BORDER
        ln.line.width = Pt(1)
        # chapter progress dots (8 dots, current filled) — replaces the ribbon
        seg = (EMU_W - Inches(1.1)) / 8
        for i in range(8):
            x = int(Inches(0.55) + i * seg)
            active = (i == chapter_idx)
            r = Inches(0.07 if not active else 0.10)
            self.shape(MSO_SHAPE.OVAL, x, Inches(0.085) if not active else Inches(0.065),
                       r, r, fill=ACCENT if active else BORDER, kind="bar")
        # footer
        ln2 = self.s.shapes.add_connector(1, 0, int(EMU_H - Inches(0.485)), int(EMU_W), int(EMU_H - Inches(0.485)))
        ln2.line.color.rgb = BORDER
        ln2.line.width = Pt(1)
        self.text(Inches(0.55), EMU_H - Inches(0.44), Inches(7.0), footer_left, Pt(11), TER, kind="band")
        self.text(Inches(7.0), EMU_H - Inches(0.44), Inches(5.8), "Paper Radar · 强化学习专栏", Pt(11), TER,
                  align=PP_ALIGN.RIGHT, kind="band")

    def _track(self, name, x, y, w, h, kind):
        self.shapes_audit.append({"name": name, "l": int(x), "t": int(y), "w": int(w), "h": int(h), "kind": kind})

    def shape(self, mso, x, y, w, h, fill=WHITE, line=BORDER, name="shape", kind="box"):
        sp = self.s.shapes.add_shape(mso, int(x), int(y), int(w), int(h))
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
        if line is None:
            sp.line.fill.background()
        else:
            sp.line.color.rgb = line
            sp.line.width = Pt(0.75)
        sp.shadow.inherit = False
        self._track(name, x, y, w, h, kind)
        return sp

    def rect(self, x, y, w, h, fill=WHITE, line=BORDER, name="rect", kind="box"):
        return self.shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill, line, name, kind)

    def bar(self, x, y, w, h, fill, name="bar"):
        return self.shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill, None, name, "bar")

    def text(self, x, y, w, s, size, color=INK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, name="text", kind="text", leading=1.32, font=FAM):
        pt = size.pt if hasattr(size, "pt") else size
        lines = measure_lines(s, pt, w / 914400, bold)
        h = text_h(lines, pt, leading)
        tb = self.s.shapes.add_textbox(int(x), int(y), int(w), int(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_top = tf.margin_bottom = 0
        tf.margin_left = tf.margin_right = 0
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = leading
            r = p.add_run()
            r.text = ln
            r.font.size = Pt(pt)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = font
        self._track(name, x, y, w, h, kind)
        return h

    def cursor(self):
        return self.y

    # ---- blocks (huashu-informed) -------------------------------------
    def kicker(self, topic):
        self.text(Inches(0.55), self.y, Inches(8.0), topic, Pt(13), ACCENT, True,
                  name="kicker", kind="band")
        self.y += Inches(0.34)

    def title(self, heading):
        """Assertion title: up to 2 lines at 34pt (F-pattern anchor)."""
        h = self.text(Inches(0.55), self.y, Inches(12.2), heading, Pt(34), NAVY, True,
                      name="title", leading=1.18)
        self.y += h + Inches(0.16)
        self.bar(Inches(0.55), self.y, Inches(0.9), Inches(0.05), ACCENT, name="rule")
        self.y += Inches(0.28)

    def lead(self, body):
        """Lead statement: first sentence at 18pt dark ink."""
        parts = body.split("。")
        lead = parts[0] + "。" if len(parts) > 1 else body
        rest = "".join(parts[1:]).lstrip()
        lines = measure_lines(lead, 18, 11.9)
        lines = lines[:3]
        h = self.text(Inches(0.55), self.y, Inches(11.9), lead, Pt(18), INK,
                      name="lead", leading=1.38)
        self.y += h + Inches(0.20)
        return rest

    def body(self, text, max_lines=99):
        """Detail paragraph: 16pt ink, fills remaining space (no aggressive cap)."""
        if not text:
            return
        if self.y > Inches(6.70):  # truly no room — content lives in notes
            return
        lines = measure_lines(text, 16, 12.2)
        room = int((Inches(6.95) - self.y) / Inches(0.311))
        keep = max(1, min(max_lines, room))
        shown = "\n".join(lines[:keep])
        if len(lines) > keep:
            shown += " …"
        h = self.text(Inches(0.55), self.y, Inches(12.2), shown, Pt(16), INK,
                      name="body", leading=1.40)
        self.y += h + Inches(0.12)

    def context_block(self, ctx):
        """Reading aid under the argument: setup + implication from storyboard context."""
        if isinstance(ctx, str):
            rows = [ctx.strip()] if ctx.strip() else []
        else:
            rows = [str(ctx.get(k, "")).strip() for k in ("setup", "implication")]
            rows = [r for r in rows if r]
        if not rows or self.y > Inches(6.70):
            return
        self.rect(Inches(0.55), self.y, Inches(0.5), 9144, fill=ACCENT,
                  name="ctx-rule", kind="line")
        self.y += Inches(0.14)
        for r in rows:
            if self.y > Inches(6.70):
                break
            h = self.text(Inches(0.55), self.y, Inches(12.2), r, Pt(15), SUB,
                          name="ctx", leading=1.36)
            self.y += h + Inches(0.08)

    def hero_number(self, items):
        """Fathom data anchor: first metric at 60pt, rest as small labels."""
        if not items:
            return
        first = items[0]
        h = Inches(1.35)
        self.text(Inches(0.55), self.y, Inches(12.0), str(first.get("value", "")), Pt(60), ACCENT, True,
                  name="hero-num", leading=1.0)
        self.y += h
        self.text(Inches(0.55), self.y, Inches(11.0), str(first.get("label", "")), Pt(16), INK,
                  name="hero-lab")
        self.y += Inches(0.55)
        for it in items[1:3]:
            self.text(Inches(0.55), self.y, Inches(5.9),
                      f"{it.get('value','')}  —  {it.get('label','')}", Pt(15), SUB,
                      name=f"sub-metric")
            self.y += Inches(0.38)

    def figure(self, png, caption, tag, max_h=None, dark=False):
        cap_h = self.text(Inches(0.55), self.y, Inches(12.2), f"图 {tag} ｜ {caption}", Pt(12), SUB,
                          name="fig-cap", kind="text")
        self.y += cap_h + Inches(0.10)
        budget = max_h if max_h is not None else Inches(4.6)
        pic_h = min(Inches(6.88) - self.y, budget)
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.height / im.width
        pic_h = min(pic_h, int(Inches(12.0) * ratio))
        pic_w = int(pic_h / ratio) if ratio else int(pic_h * 1.78)
        if pic_w > Inches(12.1):
            pic_w = Inches(12.1)
            pic_h = int(pic_w * ratio)
        x = int((EMU_W - pic_w) / 2)
        frame_fill = RGBColor(0x0E, 0x14, 0x20) if dark else WHITE
        self.rect(x - Inches(0.03), self.y - Inches(0.02), pic_w + Inches(0.06),
                  pic_h + Inches(0.04), fill=frame_fill, name="fig-frame", kind="frame")
        self.s.shapes.add_picture(str(png), x, int(self.y), int(pic_w), int(pic_h))
        self._track("figure", x, self.y, pic_w, pic_h, "box")
        self.y += pic_h + Inches(0.18)

    def equation(self, eq, tag, note=None):
        h = Inches(1.05)
        self.rect(Inches(0.55), self.y, Inches(12.0), h, fill=CREAM, line=BORDER,
                  name="eq-box", kind="frame")
        self.text(Inches(0.85), self.y + Inches(0.28), Inches(10.6), eq, Pt(22), INK,
                  align=PP_ALIGN.CENTER, name="eq", kind="frame", font=SERIF)
        self.text(Inches(10.8), self.y + Inches(0.66), Inches(1.5), f"（{tag}）",
                  Pt(11), SUB, align=PP_ALIGN.RIGHT, name="eq-tag", kind="frame")
        self.y += h + Inches(0.16)
        if note:
            self.body(note, max_lines=2)

    def limits(self, items, tag):
        self.text(Inches(0.55), self.y, Inches(12.0), f"表 {tag} ｜ 局限与边界", Pt(12), SUB,
                  name="lim-cap", kind="frame")
        self.y += Inches(0.32)
        for i, it in enumerate(items[:4], 1):
            head, _, note = it.partition("：")
            self.rect(Inches(0.55), self.y, Inches(12.0), Inches(0.50),
                      fill=BG2 if i % 2 == 0 else WHITE, line=BORDER, name=f"lim-row{i}", kind="frame")
            self.text(Inches(0.85), self.y + Inches(0.09), Inches(3.6), head, Pt(15), NAVY, True,
                      name=f"lim-h{i}", kind="frame")
            self.text(Inches(4.6), self.y + Inches(0.09), Inches(7.7), note, Pt(14), SUB,
                      name=f"lim-d{i}", kind="frame")
            self.y += Inches(0.50)
        self.y += Inches(0.16)

    def quote(self, text_, source):
        h = Inches(1.6)
        self.rect(Inches(1.2), self.y, Inches(10.9), h, fill=BG2, line=None, name="quote-bg", kind="frame")
        self.text(Inches(1.2), self.y + Inches(0.22), Inches(0.8), "“", Pt(54), ACCENT, True,
                  name="quote-mark", kind="frame", font=SERIF)
        self.text(Inches(2.0), self.y + Inches(0.42), Inches(9.4), text_, Pt(20), NAVY,
                  align=PP_ALIGN.CENTER, name="quote", kind="frame", font=SERIF)
        self.text(Inches(2.0), self.y + Inches(1.18), Inches(9.4), "— " + source, Pt(12), SUB,
                  align=PP_ALIGN.CENTER, name="quote-src", kind="frame")
        self.y += h + Inches(0.24)


def sect_origin(cit):
    if not cit or "图谱" in cit:
        return ""
    parts = cit.split("·")
    return f"{parts[1].strip()} · {parts[0].strip()}" if len(parts) >= 2 else cit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()
    p = pathlib.Path(args.project).resolve()
    sb = json.loads((p / "storyboard.json").read_text(encoding="utf-8"))
    sources = json.loads((p / "sources.json").read_text(encoding="utf-8"))["sources"]
    primary = next(s for s in sources if s.get("primary_paper"))
    arxiv_footer = f"arXiv:{primary.get('arxiv_id', '')} ｜ 讲解音轨见备注页"
    svg_dir = p / "deck" / "svg"
    prs = Presentation()
    prs.slide_width, prs.slide_height = EMU_W, EMU_H
    audit = Audit()
    def _short_en(t, limit=44):
        words = t.split()
        out = ""
        for w_ in words:
            trial = (out + " " + w_).strip()
            if len(trial) <= limit:
                out = trial
            else:
                break
        return out + ("…" if out != t else "")
    tagtxt = _short_en(sb["title_en"])

    # cover — hero EN title, assertion CN subtitle
    pg = PS(prs, "Paper Radar · 强化学习专栏", "", 0, f"arXiv:{primary.get('arxiv_id', '')}")
    pg.text(Inches(0.55), Inches(1.15), Inches(12.0), "论文解读 · PAPER RADAR", Pt(14), ACCENT, True,
            name="cov-kicker", kind="band")
    pg.text(Inches(0.55), Inches(1.7), Inches(12.0), sb.get("title_en", ""), Pt(34), NAVY, True,
            name="cov-title", leading=1.15)
    pg.bar(Inches(0.55), Inches(3.65), Inches(1.4), Inches(0.06), ACCENT, name="cov-rule")
    pg.text(Inches(0.55), Inches(3.95), Inches(12.0), sb["title"], Pt(26), INK,
            name="cov-cn", leading=1.3)
    pg.text(Inches(0.55), Inches(5.6), Inches(12.0),
            "、".join(sb.get("publish", {}).get("tags", [])[:4]), Pt(15), SUB, name="cov-tags")
    pg.s.notes_slide.notes_text_frame.text = "栏目说明：" + sb["title"] + "。" + sb.get("subtitle", "")
    audit.check(0, pg.shapes_audit)

    fig_n = tab_n = eq_n = 0
    fig_manifest = {}
    fmanifest = p / "paper-figures" / "manifest.json"
    if fmanifest.exists():
        fig_manifest = {f["id"]: f for f in json.loads(fmanifest.read_text(encoding="utf-8"))["figures"]}
    for i, sc in enumerate(sb["scenes"], 1):
        chapter_idx = CHAPTERS.index(TOPIC2CH.get(sc.get("topic"), "方法"))
        pg = PS(prs, tagtxt, "", chapter_idx, arxiv_footer)
        body = sc["body"]
        v = sc.get("visual") or {}
        lay = v.get("layout")
        pf = fig_manifest.get(sc.get("paper_figure"))

        if sc.get("topic") == "图谱" and i == 2:
            fig_n += 1
            pg.kicker("领域全景 · GRAPH")
            pg.title(sc["heading"])
            pg.figure(svg_dir / "global.png",
                      "强化学习领域全局图谱（数据 OpenAlex/arXiv）", fig_n, dark=True)
        elif sc.get("topic") == "图谱":
            fig_n += 1
            pg.kicker("论文定位 · GRAPH")
            pg.title(sc["heading"])
            pg.figure(svg_dir / "local.png",
                      "本期论文的局部引用网络（两跳邻域）", fig_n, dark=True)
        else:
            pg.kicker(sc.get("topic", ""))
            pg.title(sc["heading"])
            rest = pg.lead(body)
            if sc.get("diagram") == "mirror":
                pass  # v4: diagrams via paper figures preferred
            if sc.get("equation"):
                eq_n += 1
                pg.equation(sc["equation"][0], f"式 {eq_n}",
                            sc["equation"][1] if len(sc["equation"]) > 1 else None)
            if pf:
                fig_n += 1
                pg.figure(p / pf["file"],
                          f"{pf['caption']}（论文 Figure {pf['paper_figure_no']}，第 {pf['page']} 页）",
                          fig_n, max_h=Inches(4.0))
            elif lay == "metrics":
                tab_n += 1
                pg.hero_number(v.get("items", []))
            if rest:
                pg.body(rest)
            if sc.get("context"):
                pg.context_block(sc["context"])
            if lay == "limits":
                tab_n += 1
                pg.limits(v.get("items", []), tab_n)
            elif lay == "closing":
                pg.quote(v.get("quote", ""), v.get("source", ""))
            elif lay == "references":
                for it in v.get("entries", []):
                    pg.body(it, max_lines=3)
        note = sc.get("narration", "")
        if pf:
            note = (f"本页图示（论文 Figure {pf['paper_figure_no']}，第 {pf['page']} 页）："
                    f"{pf['caption']}\n\n{note}")
        pg.s.notes_slide.notes_text_frame.text = note
        audit.check(i, pg.shapes_audit)

    if audit.violations:
        print("OVERLAP AUDIT FAILED:")
        for v_ in audit.violations:
            print(" -", v_)
        sys.exit(1)
    out = p / "deck" / f"{sb['slug']}-deck.pptx"
    prs.save(str(out))
    print(f"editable PPTX (v4): {out} ({len(sb['scenes']) + 1} slides, overlap audit passed)")


if __name__ == "__main__":
    sys.exit(main())
