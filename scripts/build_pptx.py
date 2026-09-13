#!/usr/bin/env python3
"""Build the EDITABLE episode PPTX with native shapes (design v3.1).

Every element is a real PowerPoint text box / table / shape — nothing is a
baked image except knowledge-graph figures. The creator can freely edit,
move, and re-export; slide PNGs exported from this file feed the video
pipeline, making the PPTX the single visual source of truth.

Usage: python build_pptx.py <project_dir>
Output: deck/<slug>-deck.pptx (16:9, narration in speaker notes).
"""
import argparse
import json
import pathlib
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

EMU_W, EMU_H = Inches(13.333), Inches(7.5)
NAVY, ACCENT = RGBColor(0x00, 0x33, 0x66), RGBColor(0x00, 0x66, 0xCC)
INK, SUB, TER = RGBColor(0x33, 0x33, 0x33), RGBColor(0x66, 0x66, 0x66), RGBColor(0x99, 0x99, 0x99)
BG2, BORDER, WHITE = RGBColor(0xF5, 0xF7, 0xFA), RGBColor(0xD0, 0xD7, 0xE0), RGBColor(0xFF, 0xFF, 0xFF)
FAM = "Microsoft YaHei"
CHAPTERS = ["引言", "图谱", "背景", "方法", "实验", "局限", "启示", "来源"]
TOPIC2CH = {"引言": "引言", "图谱": "图谱", "背景": "背景", "问题": "背景", "转折": "背景",
            "方法": "方法", "算法": "方法", "训练": "方法", "证据": "实验", "结果": "实验",
            "局限": "局限", "边界": "局限", "启示": "启示", "参考文献": "来源"}


def wrap_cjk(text, per):
    text = str(text or "")
    return [text[i:i + per] for i in range(0, len(text), per)] or [""]


def wrap_words(text, per):
    """Word-boundary wrap for latin text; CJK chars wrap freely."""
    words = str(text or "").split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= per or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


class PS:
    """PowerPoint slide builder with cursor layout."""

    def __init__(self, prs, paper_tag, origin, chapter, footer_left):
        self.s = prs.slides.add_slide(prs.slide_layouts[6])
        self.y = Inches(0.0)
        # header
        self.rect(0, 0, EMU_W, Inches(0.60), fill=WHITE, line=None)
        self.line_h(0.702)
        self.bar(Inches(0.50), Inches(0.18), Inches(0.055), Inches(0.24), NAVY)
        self.text(Inches(0.66), Inches(0.14), Inches(6.0), Inches(0.34), paper_tag, Pt(13), SUB)
        if origin:
            self.text(Inches(6.3), Inches(0.14), Inches(6.5), Inches(0.34), origin, Pt(13), ACCENT,
                      bold=True, align=PP_ALIGN.RIGHT)
        # chapter ribbon
        self.rect(0, Inches(0.60), EMU_W, Inches(0.40), fill=BG2, line=None)
        seg = Inches(13.333 / 8)
        for i, ch in enumerate(CHAPTERS):
            x = Emu(int(Inches(0.50) + i * seg))
            active = (ch == chapter)
            if active:
                r = self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, x + Inches(0.03), Inches(0.655),
                               seg - Inches(0.06), Inches(0.29), fill=NAVY)
            self.text(x, Inches(0.665), seg, Inches(0.27), ch, Pt(10.5),
                      WHITE if active else TER, bold=active, align=PP_ALIGN.CENTER)
        self.y = Inches(1.32)
        # footer
        self.line_h(EMU_H - Inches(0.485))
        self.text(Inches(0.5), EMU_H - Inches(0.44), Inches(6.0), Inches(0.3), footer_left, Pt(10.5), TER)
        self.text(Inches(7.0), EMU_H - Inches(0.44), Inches(5.83), Inches(0.3),
                  "强化学习专栏 · Paper Radar", Pt(10.5), TER, align=PP_ALIGN.RIGHT)

    # -- primitives -----------------------------------------------------
    def shape(self, kind, x, y, w, h, fill=WHITE, line=BORDER):
        sp = self.s.shapes.add_shape(kind, int(x), int(y), int(w), int(h))
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
        if line is None:
            sp.line.fill.background()
        else:
            sp.line.color.rgb = line
            sp.line.width = Pt(0.75)
        sp.shadow.inherit = False
        return sp

    def rect(self, x, y, w, h, fill=WHITE, line=BORDER):
        return self.shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill, line)

    def bar(self, x, y, w, h, fill):
        return self.rect(x, y, w, h, fill=fill, line=None)

    def line_h(self, at, xw=EMU_W):
        ln = self.s.shapes.add_connector(1, 0, int(at), int(xw), int(at))
        ln.line.color.rgb = BORDER
        ln.line.width = Pt(1)

    def text(self, x, y, w, h, s, size, color=INK, bold=False, align=PP_ALIGN.LEFT,
             font=FAM, anchor=MSO_ANCHOR.TOP, leading=None):
        tb = self.s.shapes.add_textbox(int(x), int(y), int(w), int(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        for i, ln in enumerate(str(s).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if leading:
                p.line_spacing = leading
            r = p.add_run()
            r.text = ln
            r.font.size = size
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = font
            r.font.name = FAM if font == "Georgia" else font  # keep CJK fallback
        return tb

    def cursor(self):
        return self.y

    # -- blocks ---------------------------------------------------------
    def title(self, heading):
        lines = wrap_cjk(heading, 24)[:2]
        size = Pt(24) if len(lines[0]) <= 8 else Pt(22) if len(lines[0]) <= 12 else Pt(20)
        self.text(Inches(0.5), self.y, Inches(12.3), Inches(0.55), "\n".join(lines), size, NAVY, True)
        self.y += Inches(0.52) * len(lines) + Inches(0.10)
        self.bar(Inches(0.5), self.y, Inches(0.9), Inches(0.05), ACCENT)
        self.y += Inches(0.28)

    def thesis(self, claim):
        lines = wrap_cjk(claim, 54)[:2]
        h = Inches(0.30) + Inches(0.42) * len(lines)
        self.rect(Inches(0.5), self.y, Inches(12.33), h, fill=BG2, line=None)
        self.bar(Inches(0.5), self.y, Inches(0.07), h, NAVY)
        self.text(Inches(0.78), self.y + Inches(0.10), Inches(11.9), h, "\n".join(lines), Pt(16), NAVY, True)
        self.y += h + Inches(0.24)

    def body(self, text, size=Pt(14), per=64):
        lines = wrap_cjk(text, per)
        h = Inches(0.30) * len(lines)
        self.text(Inches(0.5), self.y, Inches(12.33), h, "\n".join(lines), size, INK, leading=1.35)
        self.y += h + Inches(0.18)

    def equation(self, eq, tag, note=None):
        h = Inches(0.95)
        self.rect(Inches(1.2), self.y, Inches(10.9), h, fill=WHITE, line=BORDER)
        self.text(Inches(1.4), self.y + Inches(0.22), Inches(9.6), Inches(0.5), eq, Pt(20), INK,
                  align=PP_ALIGN.CENTER)
        self.text(Inches(10.0), self.y + Inches(0.58), Inches(1.9), Inches(0.3), f"（{tag}）",
                  Pt(11), SUB, align=PP_ALIGN.RIGHT)
        self.y += h + Inches(0.16)
        if note:
            self.body(note, size=Pt(12.5), per=70)

    def table(self, caption, items, tag, note=None):
        self.text(Inches(0.5), self.y, Inches(12.3), Inches(0.28), f"表 {tag} ｜ {caption}", Pt(11.5), SUB)
        self.y += Inches(0.36)
        rows, cols = len(items) + 1, 2
        tbl_shape = self.s.shapes.add_table(rows, cols, int(Inches(0.5)), int(self.y),
                                            int(Inches(12.33)), int(Inches(0.42 * rows)))
        tbl = tbl_shape.table
        tbl.columns[0].width = Inches(3.6)
        tbl.columns[1].width = Inches(8.73)
        for j, htxt in enumerate(["指标", "含义与条件"]):
            c = tbl.cell(0, j)
            c.text = htxt
            p = c.text_frame.paragraphs[0]
            p.runs[0].font.size = Pt(13)
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = WHITE
            p.runs[0].font.name = FAM
            c.fill.solid()
            c.fill.fore_color.rgb = NAVY
        for i, it in enumerate(items, 1):
            for j, val in enumerate([str(it.get("value", "")), str(it.get("label", ""))]):
                c = tbl.cell(i, j)
                c.text = val
                p = c.text_frame.paragraphs[0]
                p.runs[0].font.size = Pt(13) if j else Pt(15)
                p.runs[0].font.bold = (j == 0)
                p.runs[0].font.color.rgb = NAVY if j == 0 else INK
                p.runs[0].font.name = FAM
                c.fill.solid()
                c.fill.fore_color.rgb = WHITE if i % 2 else BG2
        self.y += Inches(0.42 * rows) + Inches(0.22)
        if note:
            self.body(note, size=Pt(12.5), per=70)

    def figure(self, png, caption, tag):
        self.text(Inches(0.5), self.y, Inches(12.3), Inches(0.28), f"图 {tag} ｜ {caption}", Pt(11.5), SUB)
        self.y += Inches(0.34)
        max_h = Inches(7.0) - self.y
        pic_h = min(max_h, Inches(4.9))
        pic_w = int(pic_h * 1.7778)
        if pic_w > EMU_W - Inches(1.0):
            pic_w = EMU_W - Inches(1.0)
            pic_h = int(pic_w / 1.7778)
        x = int((EMU_W - pic_w) / 2)
        frame = self.rect(x - Inches(0.03), self.y - Inches(0.02), pic_w + Inches(0.06),
                          pic_h + Inches(0.04), fill=RGBColor(0x0E, 0x14, 0x20))
        self.s.shapes.add_picture(str(png), x, int(self.y), int(pic_w), int(pic_h))
        self.y += pic_h + Inches(0.2)

    def diagram_mirror(self, tag):
        """Empowerment/plasticity duality schematic (native, editable)."""
        self.text(Inches(0.5), self.y, Inches(12.3), Inches(0.28), f"图 {tag} ｜ empowerment 与 plasticity 的信息流对偶", Pt(11.5), SUB)
        self.y += Inches(0.40)
        cx = Inches(3.1)
        for k, (lab, left, right, note) in enumerate([
                ("empowerment（控制未来）", "动作 A", "观察 O", "I(A → O)"),
                ("plasticity（被未来改变）", "观察 O", "动作 A", "I(O → A)")]):
            yy = self.y + k * Inches(1.35)
            self.text(Inches(0.6), yy + Inches(0.28), Inches(2.3), Inches(0.4), lab, Pt(12.5), NAVY, True)
            b1 = self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, yy, Inches(1.5), Inches(0.62), fill=BG2)
            self.text(cx, yy + Inches(0.12), Inches(1.5), Inches(0.4), left, Pt(13), INK, True,
                      align=PP_ALIGN.CENTER)
            ar = self.shape(MSO_SHAPE.RIGHT_ARROW, cx + Inches(1.7), yy + Inches(0.10), Inches(3.0),
                            Inches(0.42), fill=ACCENT if k == 0 else NAVY)
            self.text(cx + Inches(1.7), yy - Inches(0.02), Inches(3.0), Inches(0.3), note, Pt(12), SUB,
                      align=PP_ALIGN.CENTER)
            b2 = self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(5.0), yy, Inches(1.5), Inches(0.62), fill=BG2)
            self.text(cx + Inches(5.0), yy + Inches(0.12), Inches(1.5), Inches(0.4), right, Pt(13), INK, True,
                      align=PP_ALIGN.CENTER)
        self.y += Inches(2.75)

    def limits(self, items, tag):
        self.text(Inches(0.5), self.y, Inches(12.3), Inches(0.28), f"表 {tag} ｜ 局限与边界", Pt(11.5), SUB)
        self.y += Inches(0.36)
        for i, it in enumerate(items[:4], 1):
            head, _, note = it.partition("：")
            self.rect(Inches(0.5), self.y, Inches(12.33), Inches(0.52),
                      fill=BG2 if i % 2 == 0 else WHITE, line=BORDER)
            self.text(Inches(0.72), self.y + Inches(0.10), Inches(0.4), Inches(0.32), f"{i}.", Pt(12.5), NAVY, True)
            self.text(Inches(1.05), self.y + Inches(0.10), Inches(3.4), Inches(0.32), head, Pt(13.5), NAVY, True)
            self.text(Inches(4.5), self.y + Inches(0.10), Inches(8.2), Inches(0.32), note, Pt(12.5), SUB)
            self.y += Inches(0.52)
        self.y += Inches(0.2)

    def quote(self, text_, source):
        self.rect(Inches(1.0), self.y, Inches(11.33), Inches(1.5), fill=BG2, line=None)
        self.text(Inches(1.3), self.y + Inches(0.25), Inches(10.7), Inches(0.7),
                  "\n".join(wrap_cjk("“" + text_ + "”", 36)[:2]), Pt(16), NAVY,
                  align=PP_ALIGN.CENTER)
        self.text(Inches(1.3), self.y + Inches(1.08), Inches(10.7), Inches(0.3), "— " + source,
                  Pt(11.5), SUB, align=PP_ALIGN.CENTER)
        self.y += Inches(1.7)


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
    n = len(sb["scenes"])
    tagtxt = sb["title_en"][:46]

    # cover
    pg = PS(prs, "强化学习专栏 · Paper Radar", "", "引言", arxiv_footer)
    pg.bar(Inches(0.5), Inches(1.5), Inches(12.33), Inches(0.03), NAVY)
    pg.text(Inches(0.5), Inches(1.75), Inches(6.0), Inches(0.35), "论文解读 · Paper Radar 专栏", Pt(14), ACCENT, True)
    en_lines = wrap_words(sb.get("title_en", ""), 44)[:2]
    pg.text(Inches(0.5), Inches(2.4), Inches(12.33), Inches(1.7), "\n".join(en_lines),
            Pt(32) if len(en_lines) < 2 else Pt(28), NAVY, True)
    pg.bar(Inches(0.5), Inches(4.05), Inches(1.2), Inches(0.05), ACCENT)
    pg.text(Inches(0.5), Inches(4.3), Inches(12.33), Inches(1.0), "\n".join(wrap_cjk(sb["title"], 30)[:2]), Pt(22), INK)
    pg.text(Inches(0.5), Inches(5.5), Inches(12.33), Inches(0.6),
            "、".join(sb.get("publish", {}).get("tags", [])) + " ｜ 讲解音轨见备注页", Pt(13), SUB)
    pg.rect(Inches(0.5), Inches(6.2), Inches(7.2), Inches(0.75), fill=BG2, line=None)
    pg.text(Inches(0.75), Inches(6.35), Inches(6.8), Inches(0.45),
            "结构 ｜ 全局图谱 → 局部定位 → 背景 → 方法 → 实验 → 局限 → 启示", Pt(12), NAVY)
    pg.s.notes_slide.notes_text_frame.text = "栏目说明：" + sb["title"] + "。" + sb.get("subtitle", "")

    fig_n = tab_n = eq_n = 0
    for i, sc in enumerate(sb["scenes"], 1):
        chapter = TOPIC2CH.get(sc.get("topic"), "方法")
        pg = PS(prs, tagtxt, sect_origin(sc.get("citation", "")), chapter, arxiv_footer)
        body = sc["body"]
        v = sc.get("visual") or {}
        lay = v.get("layout")
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
            pg.figure(svg_dir / "global.png", "强化学习领域全局图谱（节点为课题组，尺寸为实力分，连线为组间引用流；数据 OpenAlex/arXiv）", fig_n)
        elif sc.get("topic") == "图谱":
            fig_n += 1
            pg.figure(svg_dir / "local.png", "本期论文的局部引用网络（发光节点为焦点，两跳邻域，虚线为成员关系）", fig_n)
        else:
            if sc["kind"] not in ("references",):
                pg.thesis(claim)
            if rest:
                pg.body(rest)
            if sc.get("diagram") == "mirror":
                fig_n += 1
                pg.diagram_mirror(fig_n)
            if sc.get("equation"):
                eq_n += 1
                pg.equation(sc["equation"][0], f"式 {eq_n}",
                            sc["equation"][1] if len(sc["equation"]) > 1 else None)
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
                    pg.body(it, size=Pt(13), per=76)
        pg.s.notes_slide.notes_text_frame.text = sc.get("narration", "")
        if pg.cursor() > EMU_H - Inches(0.4):
            print(f"  WARN slide {i}: content bottom {pg.cursor()/914400:.2f}in")
    out = p / "deck" / f"{sb['slug']}-deck.pptx"
    prs.save(str(out))
    print(f"editable PPTX: {out} ({n + 1} slides)")


if __name__ == "__main__":
    sys.exit(main())
