#!/usr/bin/env python3
"""Rank research groups in a channel graph by citation relations.

Writes data/<channel>/group-rankings.json and prints a table.
Ranking inputs: total citations of member-authored papers in graph,
distinct authors, paper count, and in-graph citation flow received.
"""
import argparse
import json
import math
import pathlib
import sys


def rank(channel_dir):
    g = json.loads((channel_dir / "graph.json").read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]

    member_of = {}      # author -> group
    authored = {}       # author -> [paper]
    for e in edges:
        if e["rel"] == "member_of":
            member_of[e["s"]] = e["t"]
        elif e["rel"] == "authored":
            authored.setdefault(e["s"], []).append(e["t"])

    in_graph_cites = {}
    for e in edges:
        if e["rel"] == "cites":
            in_graph_cites[e["t"]] = in_graph_cites.get(e["t"], 0) + 1

    stats = {}
    for author, papers in authored.items():
        group = member_of.get(author)
        if not group:
            continue
        s = stats.setdefault(group, {"papers": set(), "authors": set(), "citations": 0, "flow": 0})
        s["authors"].add(author)
        for pk in papers:
            p = nodes.get(pk)
            if not p:
                continue
            s["papers"].add(pk)
            s["citations"] += p.get("citations", 0) or 0
            s["flow"] += in_graph_cites.get(pk, 0)

    rows = []
    for gid, s in stats.items():
        score = s["citations"] + 8 * s["flow"] * math.log2(2 + len(s["papers"]))
        rows.append({
            "group_id": gid, "group": nodes[gid]["label"], "authors": len(s["authors"]),
            "papers": len(s["papers"]), "citations": s["citations"], "in_graph_cited": s["flow"],
            "score": round(score, 1),
        })
    rows.sort(key=lambda r: -r["score"])
    out = channel_dir / "group-rankings.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'#':<3} {'group':<34} {'authors':>7} {'papers':>7} {'citations':>10} {'inGraph':>8} {'score':>10}")
    for i, r in enumerate(rows[:15], 1):
        print(f"{i:<3} {r['group'][:34]:<34} {r['authors']:>7} {r['papers']:>7} {r['citations']:>10} {r['in_graph_cited']:>8} {r['score']:>10}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    rank(pathlib.Path(args.root) / "data" / args.channel)


if __name__ == "__main__":
    sys.exit(main())
