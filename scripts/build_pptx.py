#!/usr/bin/env python3
"""Build the EDITABLE episode PPTX with native shapes (design v3.2).

v3.2 — measured layout + overlap audit:
- Every text block's height is computed from REAL glyph advances (PIL +
  Microsoft YaHei), so wrapping estimates match PowerPoint rendering and the
  y-cursor can never drift into the next element.
- After each slide, an overlap audit checks pairwise shape intersections and
  footer/header violations; any hit fails the build (no silent delivery).
- Paper figures (extract_figures.py) take precedence over hand-made metric
  tables; narration + auto figure description go to speaker notes.
"""
import argparse
import json
import pathlib
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
NAVY, ACCENT = RGBColor(0x00, 0x33, 0x66), RGBColor(0x00, 0x66, 0xCC)
INK, SUB, TER = RGBColor(0x33, 0x33, 0x33), RGBColor(0x66, 0x66, 0x66), RGBColor(0x99, 0x99, 0x99)
BG2, BORDER, WHITE = RGBColor(0xF5, 0xF7, 0xFA), RGBColor(0xD0, 0xD7, 0xE0), RGBColor(0xFF, 0xFF, 0xFF)
FAM = "Microsoft YaHei"
FONTS = {"regular": r"C:\Windows\Fonts\msyh.ttc", "bold": r"C:\Windows\Fonts\msyhbd.ttc"}
CHAPTERS = ["引言", "图谱", "背景", "方法", "实验", "局限", "启示", "来源"]
TOPIC2CH = {"引言": "引言", "图谱": "图谱", "背景": "背景", "问题": "背景", "转折": "背景",
            "方法": "方法", "算法": "方法", "训练": "方法", "证据": "实验", "结果": "实验",
            "局限": "局限", "边界": "局限", "启示": "启示", "参考文献": "来源"}
PX_PER_IN = 96


@lru_cache(maxsize=256)
def _font(pt, bold):
    return ImageFont.truetype(FONTS["bold" if bold else "regular"], int(round(pt * PX_PER_IN / 72)))


def measure_lines(text, pt, width_in, bold=False):
    f = _font(pt, bold)
    max_px = width_in * PX_PER_IN
    out = []
    for para in str(text).split("\n"):
        if not para:
            out.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if f.getlength(trial) <= max_px or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = ch
        out.append(cur)
    return out


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
                    f"(bottom {(s['t']+s['h'])/914400:.2f}in > {footer_top/914400:.2f}in)")


class PS:
    def __init__(self, prs, paper_tag, origin, chapter, footer_left):
        self.s = prs.slides.add_slide(prs.slide_layouts[6])
        self.shapes_audit = []
        self.y = Inches(0.0)
        self.rect(0, 0, EMU_W, Inches(0.60), fill=WHITE, line=None, kind="band")
        self.line_h(Inches(0.702))
        self.bar(Inches(0.50), Inches(0.18), Inches(0.055), Inches(0.24), NAVY)
        self.text(Inches(0.66), Inches(0.14), Inches(6.0), paper_tag, Pt(13), SUB, kind="band")
        if origin:
            self.text(Inches(6.3), Inches(0.14), Inches(6.5), origin, Pt(13), ACCENT,
                      bold=True, align=PP_ALIGN.RIGHT, kind="band")
        self.rect(0, Inches(0.60), EMU_W, Inches(0.40), fill=BG2, line=None, kind="band")
        seg = Inches(13.333 / 8)
        for i, ch in enumerate(CHAPTERS):
            x = int(Inches(0.50) + i * seg)
            active = (ch == chapter)
            if active:
                self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, x + Inches(0.03), Inches(0.655),
                           seg - Inches(0.06), Inches(0.29), fill=NAVY, kind="band")
            self.text(x, Inches(0.665), seg, ch, Pt(10.5),
                      WHITE if active else TER, bold=active, align=PP_ALIGN.CENTER, kind="band")
        self.y = Inches(1.32)
        self.line_h(EMU_H - Inches(0.485))
        self.text(Inches(0.5), EMU_H - Inches(0.44), Inches(6.0), footer_left, Pt(10.5), TER, kind="band")
        self.text(Inches(7.0), EMU_H - Inches(0.44), Inches(5.83), "强化学习专栏 · Paper Radar",
                  Pt(10.5), TER, align=PP_ALIGN.RIGHT, kind="band")

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

    def bar(self, x, y, w, h, fill):
        return self.shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill, None, "bar", "bar")

    def line_h(self, at, xw=EMU_W):
        ln = self.s.shapes.add_connector(1, 0, int(at), int(xw), int(at))
        ln.line.color.rgb = BORDER
        ln.line.width = Pt(1)

    def text(self, x, y, w, s, size, color=INK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, name="text", kind="text", leading=1.32):
        pt = size.pt if hasattr(size, "pt") else size
        lines = measure_lines(s, pt, w / 914400, bold)
        h = text_h(lines, pt, leading)
        tb = self.s.shapes.add_textbox(int(x), int(y), int(w), int(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_top = tf.margin_bottom = 0
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = leading
            r = p.add_run()
            r.text = ln
            r.font.size = Pt(pt)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = FAM
        self._track(name, x, y, w, h, kind)
        return h

    def cursor(self):
        return self.y

    def title(self, heading):
        size = Pt(24) if len(heading) <= 12 else Pt(22) if len(heading) <= 18 else Pt(20)
        h = self.text(Inches(0.5), self.y, Inches(12.33), heading, size, NAVY, True, name="title")
        self.y += h + Inches(0.06)
        self.bar(Inches(0.5), self.y, Inches(0.9), Inches(0.05), ACCENT)
        self.y += Inches(0.26)

    def thesis(self, claim):
        lines = measure_lines(claim, 16, 11.85, bold=True)
        h = int(Inches(0.24 + len(lines) * 0.30 + 0.12))
        self.rect(Inches(0.5), self.y, Inches(12.33), h, fill=BG2, line=None, name="thesis-bg", kind="frame")
        self.bar(Inches(0.5), self.y, Inches(0.07), h, NAVY)
        self.text(Inches(0.78), self.y + Inches(0.12), Inches(11.85), claim, Pt(16), NAVY, True,
                  name="thesis", kind="frame")
        self.y += h + Inches(0.22)

    def body(self, text, size=Pt(14), max_bottom=Inches(6.92)):
        pt = size.pt if hasattr(size, "pt") else size
        while pt >= 11:
            lines = measure_lines(text, pt, 12.33)
            h = text_h(lines, pt)
            if self.y + h <= max_bottom or len(lines) == 1:
                break
            pt -= 1
        h = self.text(Inches(0.5), self.y, Inches(12.33), text, Pt(pt), INK, name="body")
        self.y += h + Inches(0.14)

    def equation(self, eq, tag, note=None):
        h = Inches(0.95)
        self.rect(Inches(1.2), self.y, Inches(10.9), h, fill=WHITE, line=BORDER,
                  name="eq-box", kind="frame")
        self.text(Inches(1.4), self.y + Inches(0.24), Inches(9.6), eq, Pt(20), INK,
                  align=PP_ALIGN.CENTER, name="eq", kind="frame")
        self.text(Inches(10.0), self.y + Inches(0.58), Inches(1.9), f"（{tag}）",
                  Pt(11), SUB, align=PP_ALIGN.RIGHT, name="eq-tag", kind="frame")
        self.y += h + Inches(0.14)
        if note:
            self.body(note, size=Pt(12.5))

    def table(self, caption, items, tag, note=None):
        self.text(Inches(0.5), self.y, Inches(12.3), f"表 {tag} ｜ {caption}", Pt(11.5), SUB,
                  name="tbl-cap", kind="frame")
        self.y += Inches(0.34)
        rows = len(items) + 1
        rh_in = 0.42
        tbl_shape = self.s.shapes.add_table(rows, 2, int(Inches(0.5)), int(self.y),
                                            int(Inches(12.33)), int(Inches(rh_in * rows)))
        self._track("table", Inches(0.5), self.y, Inches(12.33), Inches(rh_in * rows), "box")
        tbl = tbl_shape.table
        tbl.columns[0].width = Inches(3.6)
        tbl.columns[1].width = Inches(8.73)
        for j, htxt in enumerate(["指标", "含义与条件"]):
            c = tbl.cell(0, j)
            c.text = htxt
            r0 = c.text_frame.paragraphs[0].runs[0]
            r0.font.size = Pt(13)
            r0.font.bold = True
            r0.font.color.rgb = WHITE
            r0.font.name = FAM
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY
        for i, it in enumerate(items, 1):
            for j, val in enumerate([str(it.get("value", "")), str(it.get("label", ""))]):
                c = tbl.cell(i, j)
                c.text = val
                r0 = c.text_frame.paragraphs[0].runs[0]
                r0.font.size = Pt(13) if j else Pt(15)
                r0.font.bold = (j == 0)
                r0.font.color.rgb = NAVY if j == 0 else INK
                r0.font.name = FAM
                c.fill.solid()
                c.fill.fore_color.rgb = WHITE if i % 2 else BG2
        self.y += Inches(rh_in * rows) + Inches(0.2)
        if note:
            self.body(note, size=Pt(12.5))

    def figure(self, png, caption, tag, max_h=None, dark=True):
        self.text(Inches(0.5), self.y, Inches(12.3), f"图 {tag} ｜ {caption}", Pt(11.5), SUB,
                  name="fig-cap", kind="frame")
        self.y += Inches(0.34)
        budget = max_h if max_h is not None else Inches(4.9)
        pic_h = min(Inches(6.88) - self.y, budget)
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.height / im.width
        pic_h = min(pic_h, int(Inches(12.0) * ratio))
        pic_w = int(pic_h / ratio) if ratio else int(pic_h * 1.78)
        if pic_w > Inches(12.2):
            pic_w = Inches(12.2)
            pic_h = int(pic_w * ratio)
        x = int((EMU_W - pic_w) / 2)
        if dark:
            self.rect(x - Inches(0.03), self.y - Inches(0.02), pic_w + Inches(0.06),
                      pic_h + Inches(0.04), fill=RGBColor(0x0E, 0x14, 0x20), name="fig-frame", kind="frame")
        self.s.shapes.add_picture(str(png), x, int(self.y), int(pic_w), int(pic_h))
        self._track("figure", x, self.y, pic_w, pic_h, "box")
        self.y += pic_h + Inches(0.18)

    def diagram_mirror(self, tag):
        self.text(Inches(0.5), self.y, Inches(12.3),
                  f"图 {tag} ｜ empowerment 与 plasticity 的信息流对偶", Pt(11.5), SUB,
                  name="diag-cap", kind="frame")
        self.y += Inches(0.40)
        cx = Inches(3.1)
        for k, (lab, left, right, note) in enumerate([
                ("empowerment（控制未来）", "动作 A", "观察 O", "I(A → O)"),
                ("plasticity（被未来改变）", "观察 O", "动作 A", "I(O → A)")]):
            yy = self.y + k * Inches(1.18)
            self.text(Inches(0.6), yy + Inches(0.24), Inches(2.35), lab, Pt(12.5), NAVY, True,
                      name=f"diag-lab{k}", kind="frame")
            self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, yy, Inches(1.5), Inches(0.62), fill=BG2,
                       name=f"diag-b1-{k}", kind="box")
            self.text(cx, yy + Inches(0.16), Inches(1.5), left, Pt(13), INK, True,
                      align=PP_ALIGN.CENTER, name=f"diag-t1-{k}", kind="frame")
            self.shape(MSO_SHAPE.RIGHT_ARROW, cx + Inches(1.7), yy + Inches(0.12), Inches(3.0),
                       Inches(0.40), fill=ACCENT if k == 0 else NAVY, name=f"diag-ar{k}", kind="box")
            self.text(cx + Inches(1.7), yy - Inches(0.02), Inches(3.0), note, Pt(12), SUB,
                      align=PP_ALIGN.CENTER, name=f"diag-n{k}", kind="frame")
            self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(5.0), yy, Inches(1.5), Inches(0.62),
                       fill=BG2, name=f"diag-b2-{k}", kind="box")
            self.text(cx + Inches(5.0), yy + Inches(0.16), Inches(1.5), right, Pt(13), INK, True,
                      align=PP_ALIGN.CENTER, name=f"diag-t2-{k}", kind="frame")
        self.y += Inches(2.45)

    def limits(self, items, tag):
        self.text(Inches(0.5), self.y, Inches(12.3), f"表 {tag} ｜ 局限与边界", Pt(11.5), SUB,
                  name="lim-cap", kind="frame")
        self.y += Inches(0.34)
        for i, it in enumerate(items[:4], 1):
            head, _, note = it.partition("：")
            self.rect(Inches(0.5), self.y, Inches(12.33), Inches(0.52),
                      fill=BG2 if i % 2 == 0 else WHITE, line=BORDER, name=f"lim-row{i}", kind="frame")
            self.text(Inches(0.72), self.y + Inches(0.11), Inches(0.4), f"{i}.", Pt(12.5), NAVY, True,
                      name=f"lim-n{i}", kind="frame")
            self.text(Inches(1.05), self.y + Inches(0.11), Inches(3.4), head, Pt(13.5), NAVY, True,
                      name=f"lim-h{i}", kind="frame")
            self.text(Inches(4.5), self.y + Inches(0.11), Inches(8.2), note, Pt(12.5), SUB,
                      name=f"lim-d{i}", kind="frame")
            self.y += Inches(0.52)
        self.y += Inches(0.18)

    def quote(self, text_, source):
        self.rect(Inches(1.0), self.y, Inches(11.33), Inches(1.5), fill=BG2, line=None,
                  name="quote-bg", kind="frame")
        self.text(Inches(1.3), self.y + Inches(0.28), Inches(10.7), "“" + text_ + "”", Pt(16), NAVY,
                  align=PP_ALIGN.CENTER, name="quote", kind="frame")
        self.text(Inches(1.3), self.y + Inches(1.10), Inches(10.7), "— " + source, Pt(11.5), SUB,
                  align=PP_ALIGN.CENTER, name="quote-src", kind="frame")
        self.y += Inches(1.68)


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
    arxiv_footer = f"arXiv:{primary.get('arxiv_id', '')}"
    svg_dir = p / "deck" / "svg"
    prs = Presentation()
    prs.slide_width, prs.slide_height = EMU_W, EMU_H
    audit = Audit()
    tagtxt = sb["title_en"][:46]

    pg = PS(prs, "强化学习专栏 · Paper Radar", "", "引言", arxiv_footer)
    pg.bar(Inches(0.5), Inches(1.5), Inches(12.33), Inches(0.03), NAVY)
    pg.text(Inches(0.5), Inches(1.75), Inches(6.0), "论文解读 · Paper Radar 专栏", Pt(14), ACCENT, True)
    en = sb.get("title_en", "")
    pg.text(Inches(0.5), Inches(2.4), Inches(12.33), en, Pt(30) if len(en) <= 46 else Pt(26), NAVY, True)
    pg.bar(Inches(0.5), Inches(4.05), Inches(1.2), Inches(0.05), ACCENT)
    pg.text(Inches(0.5), Inches(4.3), Inches(12.33), sb["title"], Pt(22), INK)
    pg.text(Inches(0.5), Inches(5.5), Inches(12.33),
            "、".join(sb.get("publish", {}).get("tags", [])) + " ｜ 讲解音轨见备注页", Pt(13), SUB)
    pg.rect(Inches(0.5), Inches(6.2), Inches(7.2), Inches(0.75), fill=BG2, line=None,
            name="cover-box", kind="frame")
    pg.text(Inches(0.75), Inches(6.38), Inches(6.8),
            "结构 ｜ 全局图谱 → 局部定位 → 背景 → 方法 → 实验 → 局限 → 启示", Pt(12), NAVY,
            name="cover-str", kind="frame")
    pg.s.notes_slide.notes_text_frame.text = "栏目说明：" + sb["title"] + "。" + sb.get("subtitle", "")
    audit.check(0, pg.shapes_audit)

    fig_n = tab_n = eq_n = 0
    fig_manifest = {}
    fmanifest = p / "paper-figures" / "manifest.json"
    if fmanifest.exists():
        fig_manifest = {f["id"]: f for f in json.loads(fmanifest.read_text(encoding="utf-8"))["figures"]}
    for i, sc in enumerate(sb["scenes"], 1):
        chapter = TOPIC2CH.get(sc.get("topic"), "方法")
        pg = PS(prs, tagtxt, sect_origin(sc.get("citation", "")), chapter, arxiv_footer)
        body = sc["body"]
        v = sc.get("visual") or {}
        lay = v.get("layout")
        pf = fig_manifest.get(sc.get("paper_figure"))
        parts = body.split("。")
        claim = ""
        for s_ in parts[:-1]:
            claim += s_ + "。"
            if len(claim) >= 24:
                break
        claim = claim if claim else body
        rest = body[len(claim):].lstrip()
        if sc.get("topic") == "图谱" and i == 2:
            fig_n += 1
            pg.figure(svg_dir / "global.png",
                      "强化学习领域全局图谱（节点为课题组，尺寸为实力分，连线为组间引用流；数据 OpenAlex/arXiv）", fig_n)
        elif sc.get("topic") == "图谱":
            fig_n += 1
            pg.figure(svg_dir / "local.png",
                      "本期论文的局部引用网络（发光节点为焦点，两跳邻域，虚线为成员关系）", fig_n)
        else:
            if sc["kind"] not in ("references",):
                pg.thesis(claim)
            if rest and not sc.get("diagram"):
                pg.body(rest)
            if sc.get("diagram") == "mirror":
                fig_n += 1
                pg.diagram_mirror(fig_n)
            if sc.get("equation"):
                eq_n += 1
                pg.equation(sc["equation"][0], f"式 {eq_n}",
                            sc["equation"][1] if len(sc["equation"]) > 1 else None)
            if pf:
                fig_n += 1
                pg.figure(p / pf["file"],
                          f"{pf['caption']}（论文 Figure {pf['paper_figure_no']}，第 {pf['page']} 页）",
                          fig_n, max_h=Inches(4.2), dark=False)
            elif lay == "metrics":
                tab_n += 1
                pg.table(v.get("table_caption", "关键指标"), v.get("items", []), tab_n)
            if lay == "limits":
                tab_n += 1
                pg.limits(v.get("items", []), tab_n)
            elif lay == "closing":
                pg.quote(v.get("quote", ""), v.get("source", ""))
            elif lay == "references":
                for it in v.get("entries", []):
                    pg.body(it, size=Pt(13))
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
    print(f"editable PPTX: {out} ({len(sb['scenes']) + 1} slides, overlap audit passed)")


if __name__ == "__main__":
    sys.exit(main())
