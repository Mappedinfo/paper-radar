---
name: paper-radar
description: >
  Use Paper Radar to run a daily academic video column (e.g. 强化学习专栏):
  discover classic high-cited and latest top-venue papers from OpenAlex,
  arXiv and similar platforms; build local knowledge graphs with 课题组/作者/
  论文/论点/论据 nodes and citation/membership/support edges; rank strong
  research groups by citation relations; render global and local highlighted
  graph views for video episodes; and drive the E:\bili\Bili paper-to-video
  pipeline (EasySlides decks, IndexTTS2 narration, Remotion render, release
  gates). Trigger words: 论文雷达, 强化学习专栏, paper radar, RL column,
  知识图谱, 今日论文, 每日专栏, group ranking, 谁在做强化学习.
---

# Paper Radar — automatic paper discovery → knowledge graph → video column

Paper Radar is a **project-backed skill**. This file routes tasks; the real
work lives in `scripts/`, `channels/`, `workflows/`, and `data/`. It owns
three stages:

1. **Discover** — daily fetch of (a) classic highly-cited works and
   (b) fresh top-venue works for each channel topic, from OpenAlex and arXiv.
2. **Graph** — maintain a local knowledge graph (`data/<channel>/graph.json`)
   with node types `group / author / paper / claim / evidence / venue` and
   edges `cites / authored / member_of / published_in / supports / claims`.
   Strong groups are ranked from citation relations, not guessed.
3. **Episode** — produce a Bilibili video episode: open with rendered
   **global + local highlighted graph views** (the paper's position in the
   field), then the main deck built with EasySlides, following the
   `E:\bili\Bili` gated pipeline for narration, render, preflight and upload.

## Daily routine

```bash
cd ~/.qoder/skills/paper-radar
python scripts/fetch_openalex.py --channel reinforcement-learning
python scripts/fetch_arxiv.py     --channel reinforcement-learning
python scripts/build_graph.py     --channel reinforcement-learning
python scripts/rank_groups.py     --channel reinforcement-learning
python scripts/column_report.py   --channel reinforcement-learning
```

Read `reports/<date>.md`, then follow `workflows/daily-column.md` for the
episode decision, graph renders, video production, and the skill-evolution
step (update `LESSONS.md`, commit, push).

## Hard rules

- Uploading/publishing stays behind the human gates defined in the
  `E:\bili\Bili` workflow. Paper Radar may prepare everything, never publish.
- Every number spoken in an episode must trace to a `paper` node's raw
  metadata or the source full text stored under the project directory.
- Graph renders used in episodes must be exported from `render_graph.py`
  (SVG), never hand-drawn, so the visual always reflects the actual graph.
