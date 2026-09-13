#!/usr/bin/env python3
"""Fetch latest arXiv entries for a channel (Atom API, stdlib only)."""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_via_openalex(channel_dir, cfg, today):
    """Fallback: recent arXiv preprints via OpenAlex (stable from this host)."""
    import urllib.request
    q = urllib.parse.quote(" ".join(cfg["topic_queries"][:2]))
    since = (today - dt.timedelta(days=cfg["recent"]["window_days"])).isoformat()
    url = ("https://api.openalex.org/works?filter=default.search:" + q +
           f",from_publication_date:{since},locations.source.display_name.search:arXiv"
           f"&sort=publication_date:desc&per-page={min(cfg['arxiv']['max_results'], 100)}"
           "&mailto=paper-radar@example.org")
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    works = []
    for w in data.get("results", []):
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        ax = doi.split("arxiv.")[-1] if "arxiv" in doi.lower() else ""
        abstract = ""
        inv = w.get("abstract_inverted_index")
        if inv:
            pos = {}
            for word, idxs in inv.items():
                for i in idxs:
                    pos[i] = word
            abstract = " ".join(pos[i] for i in sorted(pos))[:1200]
        works.append({
            "arxiv_id": ax or None,
            "title": w.get("display_name") or "",
            "published": (w.get("publication_date") or "")[:10],
            "authors": [(a.get("author") or {}).get("display_name") or ""
                        for a in w.get("authorships", [])],
            "abstract": abstract,
            "categories": [c.get("display_name", "") for c in (w.get("concepts") or [])][:4],
            "source": "arxiv-via-openalex",
            "doi": doi or None,
        })
    out_dir = channel_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"arxiv-{today}.json"
    out.write_text(json.dumps(works, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"arxiv (via openalex fallback): {len(works)} recent entries -> {out.name}")


def fetch(channel_dir, cfg):
    today = dt.date.today()
    out_dir = channel_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    ac = cfg["arxiv"]
    cats = " OR ".join(f"cat:{c}" for c in ac["categories"])
    query = f"({cats}) AND abs:{ac['query']}"
    url = (f"{API}?search_query={urllib.parse.quote(query)}"
           f"&sortBy=submittedDate&sortOrder=descending&max_results={ac['max_results']}")
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/0.1"})
    import time
    xml = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                xml = r.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                wait = 15 * (attempt + 1)
                print(f"arxiv 429; retrying in {wait}s ({attempt + 1}/3)", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < 3:
                wait = 10 * (attempt + 1)
                print(f"arxiv network error ({e}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"arxiv Atom API unavailable ({e}); falling back to OpenAlex arXiv index", file=sys.stderr)
            return fetch_via_openalex(channel_dir, cfg, today)
    root = ET.fromstring(xml)
    works = []
    for e in root.findall("a:entry", NS):
        arxiv_id = (e.findtext("a:id", "", NS) or "").rsplit("/", 1)[-1]
        works.append({
            "arxiv_id": re.sub(r"v\d+$", "", arxiv_id),
            "title": re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip(),
            "published": e.findtext("a:published", "", NS)[:10],
            "authors": [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)],
            "abstract": re.sub(r"\s+", " ", e.findtext("a:summary", "", NS)).strip(),
            "categories": [c.get("term") for c in e.findall("a:category", NS)],
            "source": "arxiv",
        })
    out = out_dir / f"arxiv-{today}.json"
    out.write_text(json.dumps(works, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"arxiv: {len(works)} recent entries -> {out.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--root", default=pathlib.Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    cfg = json.loads((root / "channels" / f"{args.channel}.json").read_text(encoding="utf-8"))
    fetch(root / "data" / args.channel, cfg)


if __name__ == "__main__":
    sys.exit(main())
