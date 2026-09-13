#!/usr/bin/env python3
"""Merge raw OpenAlex + arXiv snapshots into the channel knowledge graph.

Graph store: data/<channel>/graph.json
  nodes: {id: {type: paper|author|group|venue|claim|evidence, label, ...}}
  edges: [{s, t, rel: cites|authored|member_of|published_in|supports|claims}]
Incremental: re-running never loses claim/evidence nodes or hand-added edges.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def paper_key(w):
    if w.get("doi"):
        return "doi:" + w["doi"].lower()
    if w.get("arxiv_id"):
        return "arxiv:" + w["arxiv_id"]
    return "title:" + norm_title(w.get("title"))


def merge(channel_dir):
    graph_path = channel_dir / "graph.json"
    g = {"channel": channel_dir.name, "updated_at": None, "nodes": {}, "edges": []}
    if graph_path.exists():
        g = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes, edges = g["nodes"], g["edges"]
    edge_set = {(e["s"], e["t"], e["rel"]) for e in edges}

    def add_node(nid, ntype, **props):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "type": ntype, **props}
        else:
            for k, v in props.items():
                nodes[nid].setdefault(k, v)
        return nid

    def add_edge(s, t, rel):
        key = (s, t, rel)
        if s != t and key not in edge_set:
            edge_set.add(key)
            edges.append({"s": s, "t": t, "rel": rel})

    raw_files = sorted((channel_dir / "raw").glob("*.json")) if (channel_dir / "raw").exists() else []
    new_papers = 0
    for rf in raw_files:
        try:
            works = json.loads(rf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"skip {rf.name}: {e}")
            continue
        for w in works:
            pk = paper_key(w)
            existed = pk in nodes
            add_node(pk, "paper", label=(w.get("title") or "")[:180], year=w.get("year"),
                     citations=w.get("cited_by_count", 0), venue=w.get("venue") or "",
                     doi=w.get("doi"), arxiv=w.get("arxiv_id"), source=w.get("source"),
                     oa=(w.get("openalex_id") or "").rsplit("/", 1)[-1] or None)
            if not existed and w.get("source") == "openalex":
                new_papers += 1
            # venue node (openalex only; arXiv entries keep venue empty)
            if w.get("venue"):
                vid = add_node("venue:" + w["venue"].lower()[:80], "venue", label=w["venue"])
                add_edge(pk, vid, "published_in")
            # authors + groups
            for a in w.get("authorships", []):
                name = (a.get("name") or "").strip()
                if not name:
                    continue
                aid = add_node("author:" + name.lower(), "author", label=name,
                               openalex=a.get("openalex_id"))
                add_edge(aid, pk, "authored")
                for inst in (a.get("institutions") or [])[:1]:
                    gid = add_node("group:" + inst.lower()[:80], "group", label=inst)
                    add_edge(aid, gid, "member_of")
            for name in w.get("authors") or []:  # arxiv entries
                aid = add_node("author:" + name.lower(), "author", label=name)
                add_edge(aid, pk, "authored")
            # citation edges within the graph
            for ref in w.get("referenced_works") or []:
                add_edge(pk, ref.rsplit("/", 1)[-1], "cites")
    # normalize openalex ids to doi keys where both known
    id_alias = {}
    for nid, n in nodes.items():
        if n["type"] == "paper" and nid.startswith("doi:"):
            for alias in ("openalex",):
                if n.get(alias):
                    pass
    # map openalex work ids -> paper keys for cites resolution
    oa2key = {}
    for nid, n in nodes.items():
        if n["type"] == "paper" and n.get("oa"):
            oa2key[n["oa"]] = nid
    resolved = 0
    for e in edges:
        if e["rel"] == "cites" and e["t"] in oa2key:
            e["t"] = oa2key[e["t"]]
            resolved += 1
    # drop citation edges to unknown nodes (keep graph closed)
    g["edges"] = [e for e in edges if e["t"] in nodes and e["s"] in nodes]
    g["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    graph_path.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {}
    for n in nodes.values():
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    rels = {}
    for e in g["edges"]:
        rels[e["rel"]] = rels.get(e["rel"], 0) + 1
    print(f"graph: {counts} nodes, {rels} edges (+{new_papers} new papers, {resolved} cites resolved)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    merge(pathlib.Path(args.root) / "data" / args.channel)


if __name__ == "__main__":
    sys.exit(main())
