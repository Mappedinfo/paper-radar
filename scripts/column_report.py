#!/usr/bin/env python3
"""Compose the daily column report: standings, fresh papers, group rankings,
and the next-episode candidate (scored per channel episode config)."""
import argparse
import datetime as dt
import json
import math
import pathlib
import re
import sys

TOPIC = re.compile(
    r"reinforc\w* learning|policy (gradient|optimization|iteration)|actor[- ]critic|"
    r"Q-learning|DQN|PPO|SAC|TD-learning|temporal difference|reward|multi-agent|"
    r"self-play|bandit|inverse reinforcement|curiosity|intrinsic motivation|"
    r"successor feature|hierarchical reinforcement|RLHF|offline reinforcement", re.I)


def episode_score(p, venue_w, group_strength, today):
    vw = 1.0
    for name, w in venue_w.items():
        if name.lower() in (p.get("venue") or "").lower():
            vw = w
            break
    recency = 0.0
    if p.get("year"):
        recency = max(0.0, 1.0 - min((today - dt.date(p["year"], 1, 1)).days / 730.0, 1.0))
    cit = math.log10(1 + (p.get("citations") or 0))
    return 0.45 * vw + 0.25 * group_strength + 0.20 * recency + 0.10 * min(cit / 5.0, 1.0)


def build(root, channel):
    cd = root / "data" / channel
    cfg = json.loads((root / "channels" / f"{channel}.json").read_text(encoding="utf-8"))
    g = json.loads((cd / "graph.json").read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]
    rankings = json.loads((cd / "group-rankings.json").read_text(encoding="utf-8")) if (cd / "group-rankings.json").exists() else []
    top_groups = {r["group_id"]: i for i, r in enumerate(rankings[:30])}
    strength = {gid: 1.0 - 0.7 * (i / max(1, len(top_groups) - 1)) for gid, i in top_groups.items()}

    a2g = {}
    for e in edges:
        if e["rel"] == "member_of":
            a2g[e["s"]] = e["t"]
    authored = {}
    for e in edges:
        if e["rel"] == "authored":
            authored.setdefault(e["t"], []).append(e["s"])
    papers = [n for n in nodes.values() if n["type"] == "paper"]
    produced = set()
    ep = cd / "episodes.json"
    if ep.exists():
        produced = {e["paper_id"] for e in json.loads(ep.read_text(encoding="utf-8"))}

    today = dt.date.today()
    cands = []
    for p in papers:
        if not TOPIC.search(p.get("label") or ""):
            continue
        groups = {a2g.get(a) for a in authored.get(p["id"], [])} & set(strength)
        gs = max((strength[g] for g in groups), default=0.3)
        vw = cfg["episode"]["venue_weights"]
        score = episode_score(p, vw, gs, today)
        recent = (p.get("year") or 0) >= today.year - 1
        if recent and p["id"] not in produced:
            cands.append((score, p, groups))
    cands.sort(key=lambda x: -x[0])

    classic = sorted([p for p in papers if (p.get("citations") or 0) >= cfg["classic"]["min_citations"]],
                     key=lambda p: -(p.get("citations") or 0))
    lines = [f"# {cfg['name_zh']} · 每日雷达 {today.isoformat()}", "",
             f"- 图谱：{len(papers)} 篇论文 · {sum(1 for n in nodes.values() if n['type']=='author')} 位作者 · "
             f"{sum(1 for n in nodes.values() if n['type']=='group')} 个课题组 · 图内引用边 "
             f"{sum(1 for e in edges if e['rel']=='cites')}", ""]
    lines.append("## 今日候选（下一期选题）")
    for score, p, groups in cands[:8]:
        gnames = "、".join(nodes[g]["label"] for g in list(groups)[:2]) if groups else "-"
        lines.append(f"- **{score:.2f}** {p['label'][:80]}（{p.get('venue') or 'arXiv'} {p.get('year')}，被引 {p.get('citations', 0)}，{gnames}）`{p['id']}`")
    lines.append("\n## 经典高被引 TOP 10")
    for p in classic[:10]:
        lines.append(f"- {p['label'][:80]}（{p.get('year')}，被引 {p.get('citations', 0)}）")
    lines.append("\n## 课题组实力榜 TOP 10")
    for i, r in enumerate(rankings[:10], 1):
        lines.append(f"- {i}. {r['group']} · {r['papers']} 篇 · 总被引 {r['citations']} · 图内被引 {r['in_graph_cited']} · 分 {r['score']}")
    lines.append(f"\n## 渲染命令\n```\npython scripts/render_graph.py --channel {channel} --mode global\n"
                 f"python scripts/render_graph.py --channel {channel} --mode local --focus <候选的paper id>\n```")
    out = root / "reports" / f"{channel}-{today.isoformat()}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"report: {out}")
    if cands:
        print(f"next-episode candidate: [{cands[0][1]['id']}] {cands[0][1]['label'][:70]} (score {cands[0][0]:.2f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    build(pathlib.Path(args.root), args.channel)


if __name__ == "__main__":
    sys.exit(main())
