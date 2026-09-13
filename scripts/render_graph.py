#!/usr/bin/env python3
"""Render knowledge-graph views as SVG for video episodes.

Modes:
  --mode global            group-level map: top groups sized by strength,
                           inter-group citation flow edges (who cites whom).
  --mode local --focus ID [--hops 2] [--highlight id1,id2]
                           ego network around a paper/author/group with the
                           focus node glowing, edge relation labels, and the
                           rest of the graph dimmed for context.

Deterministic layout (no deps). Output: data/<channel>/renders/*.svg
"""
import argparse
import json
import math
import pathlib
import sys
from xml.sax.saxutils import escape

STYLE = {
    "group":   {"fill": "#F5B84A", "stroke": "#8A5A00", "label": "#F5B84A"},
    "paper":   {"fill": "#4AC6F5", "stroke": "#0B5470", "label": "#BFE9F8"},
    "author":  {"fill": "#B08CF2", "stroke": "#4A2E86", "label": "#DCD0FA"},
    "venue":   {"fill": "#9AA5B1", "stroke": "#3E4854", "label": "#C9D2DB"},
    "claim":   {"fill": "#F27E9D", "stroke": "#7E2743", "label": "#F9CFDB"},
    "evidence":{"fill": "#7ED9A0", "stroke": "#1E6B42", "label": "#CDF0DC"},
}
W, H = 1920, 1080
REL_ZH = {"cites": "引用", "authored": "著文", "member_of": "属于", "published_in": "刊于", "supports": "支撑", "claims": "主张"}


def esc(s):
    return escape(str(s or ""))


def wrap(text, n=26, lines=2):
    text = str(text or "")
    if len(text) <= n:
        return [text]
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= n:
            out.append(cur)
            cur = ""
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    if len(text) > n * lines:
        out[-1] = out[-1][: n - 1] + "…"
    return out


class Canvas:
    def __init__(self, title, subtitle):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '<defs>'
            '<filter id="glow"><feGaussianBlur stdDeviation="9" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="soft"><feGaussianBlur stdDeviation="4" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '</defs>',
            f'<rect width="{W}" height="{H}" fill="#0E1420"/>',
            f'<text x="60" y="70" fill="#F2F6FA" font-family="Georgia, \'Songti SC\', serif" font-size="34" font-weight="bold">{esc(title)}</text>',
            f'<text x="60" y="108" fill="#8FA0B3" font-family="Georgia, serif" font-size="19">{esc(subtitle)}</text>',
        ]

    def line(self, x1, y1, x2, y2, stroke="#3A4A61", w=1.4, opacity=1.0, dashed=False, arrow=False):
        d = ' stroke-dasharray="7 6"' if dashed else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="{stroke}" stroke-width="{w}" opacity="{opacity}"{d}/>')
        if arrow:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ang = math.atan2(y2 - y1, x2 - x1)
            ax, ay = mx - 9 * math.cos(ang), my - 9 * math.sin(ang)
            self.parts.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="3.2" fill="{stroke}" opacity="{opacity}"/>')

    def node(self, x, y, r, ntype, label_lines, glow=False, dim=False, sub=""):
        st = STYLE.get(ntype, STYLE["venue"])
        op = 0.35 if dim else 1.0
        f = ' filter="url(#glow)"' if glow else ""
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{st["fill"]}" '
                          f'stroke="{st["stroke"]}" stroke-width="2" opacity="{op}"{f}/>')
        fs = 17 if len(label_lines) > 1 else 18
        ty = y + r + 24
        for ln in label_lines:
            self.parts.append(f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{st["label"]}" '
                              f'font-family="Georgia, serif" font-size="{fs}" opacity="{op}">{esc(ln)}</text>')
            ty += fs + 4
        if sub:
            self.parts.append(f'<text x="{x:.1f}" y="{y - r - 10:.1f}" text-anchor="middle" fill="{st["label"]}" '
                              f'font-family="Georgia, serif" font-size="16" opacity="{op}">{esc(sub)}</text>')

    def edge_label(self, x, y, text, color="#9FB2C8"):
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" fill="{color}" '
                          f'font-family="Georgia, serif" font-size="15">{esc(text)}</text>')

    def legend(self, entries, note=""):
        x, y = 60, H - 46 - 34 * len(entries)
        for t, lab in entries:
            st = STYLE[t]
            self.parts.append(f'<circle cx="{x+8}" cy="{y}" r="8" fill="{st["fill"]}" stroke="{st["stroke"]}"/>')
            self.parts.append(f'<text x="{x+26}" y="{y+6}" fill="{st["label"]}" font-family="Georgia, serif" font-size="17">{esc(lab)}</text>')
            y += 34
        if note:
            self.parts.append(f'<text x="{x}" y="{H-28}" fill="#6E8098" font-family="Georgia, serif" font-size="16">{esc(note)}</text>')

    def save(self, path):
        self.parts.append("</svg>")
        path.write_text("\n".join(self.parts), encoding="utf-8")
        print(f"rendered: {path}")


def paper_group(nodes, edges):
    a2g, a2p = {}, {}
    for e in edges:
        if e["rel"] == "member_of":
            a2g[e["s"]] = e["t"]
        elif e["rel"] == "authored":
            a2p.setdefault(e["s"], []).append(e["t"])
    p2g = {}
    for a, ps in a2p.items():
        g = a2g.get(a)
        if g:
            for p in ps:
                p2g[p] = g
    return p2g


def render_global(channel_dir, top_n=12):
    g = json.loads((channel_dir / "graph.json").read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]
    rankings = []
    rp = channel_dir / "group-rankings.json"
    if rp.exists():
        rankings = json.loads(rp.read_text(encoding="utf-8"))
    top = [r for r in rankings if any(n["id"] == r["group_id"] for n in nodes.values())][:top_n]
    if not top:
        top = [{"group_id": k, "group": v["label"], "score": 1, "papers": 1}
               for k, v in list(nodes.items()) if v["type"] == "group"][:top_n]
    p2g = paper_group(nodes, edges)
    flow = {}
    for e in edges:
        if e["rel"] == "cites":
            gs, gt = p2g.get(e["s"]), p2g.get(e["t"])
            if gs and gt and gs != gt:
                flow[(gs, gt)] = flow.get((gs, gt), 0) + 1
    ids = [r["group_id"] for r in top]
    max_score = max((r.get("score", 1) for r in top), default=1)
    cx, cy, R = W / 2, H / 2 + 20, 330
    pos = {}
    for i, gid in enumerate(ids):
        ang = -math.pi / 2 + 2 * math.pi * i / len(ids)
        pos[gid] = (cx + R * math.cos(ang), cy + R * math.sin(ang))
    c = Canvas(f"{g['channel']} · 领域全局图", f"top {len(ids)} 课题组 · 节点大小=实力分 · 连线=组间引用流 · {g['updated_at'][:10]}")
    maxw = max(flow.values(), default=1)
    for (gs, gt), w in flow.items():
        if gs in pos and gt in pos:
            x1, y1 = pos[gs]
            x2, y2 = pos[gt]
            c.line(x1, y1, x2, y2, stroke="#31435C", w=1 + 5 * w / maxw, opacity=0.25 + 0.5 * w / maxw, arrow=True)
    for r in top:
        gid = r["group_id"]
        x, y = pos[gid]
        rad = 16 + 34 * math.sqrt((r.get("score", 1) or 1) / max_score)
        c.node(x, y, rad, "group", wrap(r["group"], 22, 2), sub=f"{r.get('papers', '?')}篇 · 引{r.get('citations', 0)}")
    c.legend([("group", "课题组"), ("paper", "论文"), ("author", "作者"),
              ("claim", "论点"), ("evidence", "论据")],
             note=f"共 {sum(1 for n in nodes.values() if n['type']=='paper')} 篇论文 · {len(ids)} 个头部课题组 · 数据源 OpenAlex/arXiv")
    out_dir = channel_dir / "renders"
    out_dir.mkdir(exist_ok=True)
    c.save(out_dir / "global.svg")


def render_local(channel_dir, focus, hops=2, highlight=()):
    g = json.loads((channel_dir / "graph.json").read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]
    if focus not in nodes:
        cands = [i for i, n in nodes.items() if n["type"] == "paper"][:1]
        print(f"focus {focus} not found; examples: {cands}", file=sys.stderr)
        sys.exit(2)
    adj = {}
    for e in edges:
        adj.setdefault(e["s"], []).append((e["t"], e))
        adj.setdefault(e["t"], []).append((e["s"], e))
    # BFS by hops
    frontier = {focus}
    layers = {0: {focus}}
    for h in range(1, hops + 1):
        nxt = set()
        for n in layers[h - 1]:
            for nb, _ in adj.get(n, []):
                if nb not in layers.get(h - 1, ()) and all(nb not in layers[k] for k in range(h)):
                    nxt.add(nb)
        layers[h] = nxt
        if not nxt:
            break
    sub = set().union(*layers.values())
    relabeled = set(highlight) | {focus}
    c = Canvas(f"{nodes[focus]['label'][:46]}", f"局部视图 · {hops} 跳邻域 · {len(sub)} 节点 · 高亮=当前讲述对象")
    cx, cy = W / 2, H / 2
    # radial by hop layer
    pos = {focus: (cx, cy)}
    rings = [(cx, cy, 210, 0), (cx, cy, 380, 0), (cx, cy, 520, 0), (cx, cy, 640, 0)]
    for h in range(1, hops + 1):
        members = sorted(layers.get(h, set()))
        if not members:
            break
        _, _, rr, _ = rings[min(h, len(rings) - 1)]
        full = 2 * math.pi if h == 1 else 2 * math.pi
        for i, nid in enumerate(members[: 14 if h == 1 else 18]):
            ang = -math.pi / 2 + full * i / min(len(members), 14 if h == 1 else 18)
            pos[nid] = (cx + rr * math.cos(ang), cy + rr * math.sin(ang))
    in_sub_edges = [e for e in edges if e["s"] in pos and e["t"] in pos]
    for e in in_sub_edges:
        hot = e["s"] in relabeled or e["t"] in relabeled
        x1, y1 = pos[e["s"]]
        x2, y2 = pos[e["t"]]
        c.line(x1, y1, x2, y2, stroke="#C99A3F" if hot else "#3A4A61", w=2.2 if hot else 1.3,
               opacity=0.95 if hot else 0.5, arrow=e["rel"] == "cites", dashed=e["rel"] == "member_of")
        if e["s"] == focus or e["t"] == focus:
            c.edge_label((x1 + x2) / 2, (y1 + y2) / 2 - 8, REL_ZH.get(e["rel"], e["rel"]), "#E8C87A")
    for nid, (x, y) in pos.items():
        n = nodes[nid]
        r = 44 if nid == focus else (26 if nid in relabeled else 20)
        if n["type"] == "group":
            r += 4
        c.node(x, y, r, n["type"], wrap(n.get("label", ""), 18 if nid == focus else 14, 2 if nid == focus else 1),
               glow=nid == focus or nid in highlight, dim=nid not in relabeled and nid != focus,
               sub=(f"被引 {n.get('citations', '?')}" if n["type"] == "paper" and nid == focus else
                    (str(n.get("year") or "") if n["type"] == "paper" else "")))
    c.legend([("group", "课题组"), ("author", "作者"), ("paper", "论文"), ("claim", "论点"), ("evidence", "论据")],
             note="实线箭头=引用 · 虚线=成员关系 · 发光=高亮")
    out_dir = channel_dir / "renders"
    out_dir.mkdir(exist_ok=True)
    fn = focus.replace("/", "_").replace(":", "-")[-60:]
    c.save(out_dir / f"local-{fn}.svg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    ap.add_argument("--mode", choices=["global", "local"], default="global")
    ap.add_argument("--focus")
    ap.add_argument("--hops", type=int, default=2)
    ap.add_argument("--highlight", default="")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()
    cd = pathlib.Path(args.root) / "data" / args.channel
    if args.mode == "global":
        render_global(cd, args.top)
    else:
        if not args.focus:
            sys.exit("--focus required for local mode")
        render_local(cd, args.focus, args.hops, tuple(x for x in args.highlight.split(",") if x))


if __name__ == "__main__":
    sys.exit(main())
