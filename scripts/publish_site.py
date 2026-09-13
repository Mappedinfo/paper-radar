#!/usr/bin/env python3
"""Publish the channel graph to the GitHub Pages site under docs/data/.

The site stores relationships, claims and evidence only — never paper content.
This script also seeds claim/evidence nodes from episodes already produced by
the E:\bili\Bili pipeline (their sources.json claims passed all production
gates, so they are pre-verified), listed in channels/<channel>.json under
"episode_claims".

Run after build_graph/rank_groups, before commit+push.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

BILI_PROJECTS = pathlib.Path(r"E:\bili\Bili\projects")


def seed_claims(root, channel, graph):
    cfg = json.loads((root / "channels" / f"{channel}.json").read_text(encoding="utf-8"))
    seeds = cfg.get("episode_claims", [])
    nodes, edges = graph["nodes"], graph["edges"]
    edge_set = {(e["s"], e["t"], e["rel"]) for e in edges}

    def add_node(nid, ntype, **props):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "type": ntype, **props}
        return nid

    def add_edge(s, t, rel):
        if s != t and (s, t, rel) not in edge_set:
            edge_set.add((s, t, rel))
            edges.append({"s": s, "t": t, "rel": rel})

    added = 0
    for seed in seeds:
        src_path = BILI_PROJECTS / seed["slug"] / "sources.json"
        if not src_path.exists():
            print(f"seed skip (no sources.json): {seed['slug']}")
            continue
        src = json.loads(src_path.read_text(encoding="utf-8"))
        primary = next((s for s in src.get("sources", []) if s.get("primary_paper")), None)
        if not primary:
            continue
        pk = seed["paper_id"]
        add_node(pk, "paper", label=primary.get("title", seed["slug"])[:180],
                 year=primary.get("year"), citations=primary.get("cited_by_count", 0) or 0,
                 venue=primary.get("venue") or "arXiv", source="episode",
                 episode=seed["slug"])
        for name in primary.get("authors", [])[:12]:
            aid = add_node("author:" + name.lower(), "author", label=name)
            add_edge(aid, pk, "authored")
        for i, claim in enumerate(primary.get("claims", [])[:6], 1):
            cid = add_node(f"claim:{seed['slug']}:{i}", "claim", label=claim.strip())
            add_edge(pk, cid, "claims")
            added += 1
        # evidence nodes from the episode's verified numeric claims (configured)
        for ev in seed.get("evidence", []):
            eid = add_node(f"evidence:{seed['slug']}:{ev['n']}", "evidence", label=ev["label"])
            add_edge(eid, f"claim:{seed['slug']}:{ev['n']}", "supports")
            added += 1
    return added


def publish(root, channel):
    cd = root / "data" / channel
    graph = json.loads((cd / "graph.json").read_text(encoding="utf-8"))
    n_claims = seed_claims(root, channel, graph)
    (cd / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")

    out = root / "docs" / "data"
    out.mkdir(parents=True, exist_ok=True)
    slim_nodes = {}
    for nid, n in graph["nodes"].items():
        slim_nodes[nid] = {k: n.get(k) for k in ("id", "type", "label", "year", "citations", "venue")}
    payload = {
        "channel": channel,
        "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "nodes": slim_nodes,
        "edges": graph["edges"],
    }
    (out / f"{channel}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    rp = cd / "group-rankings.json"
    if rp.exists():
        (out / f"{channel}-rankings.json").write_text(rp.read_text(encoding="utf-8"), encoding="utf-8")
    counts = {}
    for n in slim_nodes.values():
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    print(f"site data: docs/data/{channel}.json — {counts} nodes, {len(payload['edges'])} edges (+{n_claims} claim/evidence seeded)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    publish(pathlib.Path(args.root), args.channel)


if __name__ == "__main__":
    sys.exit(main())
