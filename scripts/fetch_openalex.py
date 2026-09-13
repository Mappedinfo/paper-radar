#!/usr/bin/env python3
"""Fetch classic high-cited and recent top-venue works from OpenAlex for a channel.

Writes raw works to data/<channel>/raw/openalex-<classic|recent>-<date>.json
Stdlib only. Polite pool via mailto param.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://api.openalex.org/works"
MAILTO = "paper-radar@example.org"
UA = "paper-radar/0.1 (github.com/mappedinfo/paper-radar)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


RL_TITLE = __import__("re").compile(
    r"reinforc\w* learning|\bRL\b|policy (gradient|optimization|iteration)|"
    r"actor[- ]critic|Q-learning|A3C|DQN|PPO|SAC|TD-learning|temporal difference|"
    r"reward|multi-agent|self-play|bandit|apprenticeship|inverse reinforcement|"
    r"curiosity|intrinsic motivation|successor feature|options framework|"
    r"exploration and exploitation|empowerment|hierarchical reinforcement", __import__("re").I)


def plausible(w):
    """Reject OpenAlex citation-count outliers and off-topic titles."""
    import datetime as dtm
    year = w.get("publication_year") or 0
    cites = w.get("cited_by_count", 0) or 0
    if year:
        years = max(1, dtm.date.today().year - year + 1)
        if cites / years > 12000:  # faster than any real paper accumulates
            return False
    return True


def slim(work):
    """Keep only fields the graph needs."""
    authorships = []
    for a in work.get("authorships", []):
        insts = []
        for key in ("institutions", "affiliations"):
            for inst in a.get(key) or []:
                name = inst.get("display_name") if isinstance(inst, dict) else None
                if name:
                    insts.append(name)
        if not insts:
            insts = [s.strip() for s in (a.get("raw_affiliation_strings") or []) if s and s.strip()][:1]
        authorships.append({
            "name": (a.get("author") or {}).get("display_name") or a.get("raw_author_name") or "",
            "openalex_id": (a.get("author") or {}).get("id"),
            "institutions": insts,
        })
    venue = ""
    for loc in (work.get("primary_location"), *(work.get("locations") or [])):
        if loc and loc.get("source") and loc["source"].get("display_name"):
            venue = loc["source"]["display_name"]
            break
    return {
        "openalex_id": work.get("id"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
        "title": work.get("display_name") or work.get("title") or "",
        "year": work.get("publication_year"),
        "cited_by_count": work.get("cited_by_count", 0),
        "venue": venue,
        "authorships": authorships,
        "referenced_works": (work.get("referenced_works") or [])[:80],
        "abstract_inverted_index": work.get("abstract_inverted_index"),
        "source": "openalex",
    }


def fetch(channel_dir, cfg):
    today = dt.date.today()
    out_dir = channel_dir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    classic = cfg["classic"]
    q = urllib.parse.quote(classic["search"])
    url = (f"{API}?filter=default.search:{q},cited_by_count:>{classic['min_citations']}"
           f"&sort=cited_by_count:desc&per-page=100&mailto={MAILTO}")
    works, cursor = [], None
    while len(works) < classic["max_works"]:
        page_url = url + (f"&cursor={cursor}" if cursor else "")
        data = get(page_url)
        batch = [slim(w) for w in data.get("results", [])
                 if plausible(w) and RL_TITLE.search(w.get("display_name") or "")]
        works += batch
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor or not batch:
            break
    (out_dir / f"openalex-classic-{today}.json").write_text(
        json.dumps(works[: classic["max_works"]], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"classic: {min(len(works), classic['max_works'])} works (>{classic['min_citations']} citations)")

    recent = cfg["recent"]
    since = (today - dt.timedelta(days=recent["window_days"])).isoformat()
    q = urllib.parse.quote(" ".join(cfg["topic_queries"][:2]))
    url = (f"{API}?filter=default.search:{q},from_publication_date:{since}"
           f"&sort=cited_by_count:desc&per-page=100&mailto={MAILTO}")
    works, cursor, seen = [], None, set()
    while len(works) < recent["max_works"] * 2:
        page_url = url + (f"&cursor={cursor}" if cursor else "")
        data = get(page_url)
        batch = [slim(w) for w in data.get("results", [])]
        if not batch:
            break
        for w in batch:
            vl = (w["venue"] or "").lower()
            if vl and any(v.lower() in vl for v in recent["venues"]) and w["openalex_id"] not in seen \
                    and RL_TITLE.search(w["title"] or ""):
                seen.add(w["openalex_id"])
                works.append(w)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    (out_dir / f"openalex-recent-{today}.json").write_text(
        json.dumps(works[: recent["max_works"]], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"recent (top venues, last {recent['window_days']}d): {min(len(works), recent['max_works'])} works")


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
