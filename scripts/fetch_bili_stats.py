#!/usr/bin/env python3
"""Fetch per-video Bilibili stats for every episode in episodes.json.

Usage: python fetch_bili_stats.py --channel reinforcement-learning [--out reports/video-stats.json]

Note: the old `archive/stat` endpoint returns 404 since 2026-10; use
`x/web-interface/view?bvid=` which returns the full archive including stat.
"""
import argparse
import io
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json",
}


def fetch(channel, out):
    episodes = json.loads((ROOT / "data" / channel / "episodes.json").read_text(encoding="utf-8"))
    rows = []
    for i, e in enumerate(episodes):
        bvid = e["bvid"]
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            if d.get("code") == 0:
                s = d["data"]["stat"]
                rows.append({
                    "date": e["date"], "slug": e["slug"], "bvid": bvid,
                    "title": d["data"].get("title", "")[:60],
                    "duration_s": d["data"].get("duration", 0),
                    "view": s.get("view", 0), "danmaku": s.get("danmaku", 0),
                    "reply": s.get("reply", 0), "favorite": s.get("favorite", 0),
                    "coin": s.get("coin", 0), "share": s.get("share", 0),
                    "like": s.get("like", 0),
                })
                print(f"{i+1:3d} {e['slug'][:34]:36s} v={s.get('view',0):6d} like={s.get('like',0):4d} fav={s.get('favorite',0):4d}")
            else:
                rows.append({"date": e["date"], "slug": e["slug"], "bvid": bvid, "error": d.get("code"), "msg": d.get("message", "")})
                print(f"{i+1:3d} {e['slug'][:34]:36s} code={d.get('code')}")
        except Exception as ex:
            rows.append({"date": e["date"], "slug": e["slug"], "bvid": bvid, "error": str(ex)})
            print(f"{i+1:3d} {e['slug'][:34]:36s} ERR {ex}")
        time.sleep(1.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for r in rows if "view" in r)
    print(f"saved {ok}/{len(rows)} records -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="reinforcement-learning")
    ap.add_argument("--out", default=None, help="output json path (default reports/video-stats-<date>.json)")
    args = ap.parse_args()
    import datetime
    out = pathlib.Path(args.out) if args.out else ROOT / "reports" / f"video-stats-{datetime.date.today():%Y-%m-%d}.json"
    fetch(args.channel, out)


if __name__ == "__main__":
    main()
