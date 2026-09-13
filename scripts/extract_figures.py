#!/usr/bin/env python3
"""Extract paper figures by rendering the paper PDF (v2, PDF-screenshot based).

Per the creator's direction: download the arXiv PDF and crop figures from the
rendered pages instead of parsing HTML.

Method (deterministic, PyMuPDF):
  1. Download https://arxiv.org/pdf/<id> -> paper.pdf (skip if present).
  2. On each page, find caption text blocks ("Figure N ..." / "图 N ...").
  3. The figure region is the union of image XObjects + vector-drawing
     clusters that sit above the caption and near it vertically.
  4. Crop at 2.5x zoom -> paper-figures/fig-NN.png (no extra cropping needed;
     the clip rect is already tight).
  5. Classify by caption keywords (architecture/results/other), auto-assign to
     storyboard scenes (method <- architecture, evidence <- results), and
     write the visual-assets.json rights ledger.

Usage: python extract_figures.py <project_dir> [--arxiv-id 2609.10776]
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.request

ARCH_KW = re.compile(r"architect|framework|overview|pipeline|schematic|environment|benchmark environment|model of|illustrat|结构|架构|流程|示意", re.I)
RES_KW = re.compile(r"\bresults?\b|performance|accuracy|comparison|ablation|landscape|frontier|converg|score|curve|simulation|结果|性能|对比|收敛", re.I)
CAP_RE = re.compile(r"^\s*(Figure|Fig\.?|图)\s*(\d+)", re.I)
ZOOM = 2.5


def download_pdf(project, arxiv_id):
    pdf = project / "paper.pdf"
    if pdf.exists() and pdf.stat().st_size > 10000:
        return pdf
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        pdf.write_bytes(r.read())
    print(f"downloaded {url} ({pdf.stat().st_size // 1024} KB)")
    return pdf


def page_figures(page):
    """Yield (figure_no, caption_text, clip_rect) for one PDF page."""
    d = page.get_text("dict")
    caps = []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        text = " ".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
        m = CAP_RE.match(text)
        if m:
            caps.append((int(m.group(2)), text, fitz_rect(b["bbox"])))
    if not caps:
        return
    # text blocks excluding captions — regions mostly covered by them are body text
    text_rects = [fitz_rect(b["bbox"]) for b in d["blocks"] if b.get("type") == 0]
    cap_rects = [c[2] for c in caps]
    body_texts = [t for t in text_rects if not any(t.intersects(c) for c in cap_rects)]
    # candidate graphic regions
    regions = []
    try:
        regions += [fitz_rect(r) for r in page.cluster_drawings()]
    except Exception:
        pass
    for info in page.get_image_info():
        regions.append(fitz_rect(info["bbox"]))

    def mostly_text(r):
        for t in body_texts:
            inter = r & t
            if not inter.is_empty and inter.get_area() > 0.35 * max(r.get_area(), 1):
                return True
        return False

    for fno, cap, cr in caps:
        band = [r for r in regions
                if r.y1 <= cr.y0 + 12 and r.y1 > cr.y0 - 250 and r.get_area() > 1500
                and not mostly_text(r)]
        if not band:
            # caption ABOVE figure (rare): try below
            band = [r for r in regions if r.y0 >= cr.y1 - 12 and r.y0 < cr.y1 + 250
                    and r.get_area() > 1500 and not mostly_text(r)]
        if not band:
            continue
        u = band[0]
        for r in band[1:]:
            u |= r
        u = fitz_rect(max(20, u.x0 - 6), max(20, u.y0 - 6),
                      min(page.rect.x1 - 20, u.x1 + 6), min(cr.y0 - 2, u.y1 + 6))
        if u.width < 60 or u.height < 40:
            continue
        yield fno, cap, u


def fitz_rect(*args):
    import fitz
    if len(args) == 1:
        return fitz.Rect(args[0])
    return fitz.Rect(*args)


def extract(project, arxiv_id):
    import fitz
    pdf = download_pdf(project, arxiv_id)
    doc = fitz.open(pdf)
    outdir = project / "paper-figures"
    outdir.mkdir(exist_ok=True)
    figures = []
    mat = fitz.Matrix(ZOOM, ZOOM)
    for pno, page in enumerate(doc, 1):
        for fno, cap, clip in page_figures(page):
            pix = page.get_pixmap(matrix=mat, clip=clip)
            fid = f"fig-{fno:02d}"
            path = outdir / f"{fid}.png"
            pix.save(path)
            cap_clean = re.sub(r"\s+", " ", cap).strip()
            ftype = "results" if RES_KW.search(cap_clean) else (
                "architecture" if ARCH_KW.search(cap_clean) else "other")
            figures.append({"id": fid, "paper_figure_no": fno, "page": pno,
                            "caption": cap_clean[:200], "type": ftype,
                            "source_url": f"arXiv:{arxiv_id} PDF p{pno} Figure {fno}",
                            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
                            "file": str(path.relative_to(project)),
                            "size": [pix.width, pix.height]})
            print(f"  {fid} [p{pno} {ftype}] Figure {fno}: {cap_clean[:64]}")
    figures.sort(key=lambda f: f["paper_figure_no"])
    if not figures:
        print("no figures found")
        return []

    sb_path = project / "storyboard.json"
    sb = json.loads(sb_path.read_text(encoding="utf-8")) if sb_path.exists() else {"scenes": []}
    for sc in sb.get("scenes", []):
        sc.pop("paper_figure", None)
    assigned = {}
    for f in figures:
        target = None
        if f["type"] == "architecture":
            target = next((s for s in sb["scenes"] if s.get("kind") == "method" and "paper_figure" not in s), None)
        elif f["type"] == "results":
            target = next((s for s in sb["scenes"] if s.get("kind") == "evidence" and "paper_figure" not in s), None)
        if target is None:
            continue
        target["paper_figure"] = f["id"]
        assigned[f["id"]] = target["heading"]
    (outdir / "manifest.json").write_text(
        json.dumps({"arxiv_id": arxiv_id, "figures": figures, "assigned": assigned},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    if sb.get("scenes"):
        sb_path.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    ledger = {"visuals": []}
    va = project / "visual-assets.json"
    if va.exists():
        try:
            ledger = json.loads(va.read_text(encoding="utf-8"))
        except Exception:
            pass
    known = {v.get("source_url") for v in ledger.get("visuals", [])}
    for f in figures:
        if f["source_url"] in known:
            continue
        ledger["visuals"].append({
            "asset": f["file"], "source_url": f["source_url"],
            "acquisition": f"arXiv PDF page {f['page']} rendered at {ZOOM}x, caption-anchored clip",
            "transformation": "PyMuPDF clip crop (no resample beyond zoom)",
            "source_sha256": f["source_sha256"], "on_slide_use": f["type"],
            "caption": f["caption"],
            "rights": "arXiv non-exclusive license; interpretive commentary; human gate at submission"})
    va.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"extracted {len(figures)} figures from PDF; assigned {len(assigned)}; ledger {len(ledger['visuals'])}")
    return figures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--arxiv-id")
    args = ap.parse_args()
    p = pathlib.Path(args.project).resolve()
    aid = args.arxiv_id
    if not aid:
        src = json.loads((p / "sources.json").read_text(encoding="utf-8"))["sources"]
        aid = next(s for s in src if s.get("primary_paper")).get("arxiv_id")
    extract(p, aid)


if __name__ == "__main__":
    sys.exit(main())
