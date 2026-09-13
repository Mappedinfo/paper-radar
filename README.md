# Paper Radar 📡

自动发现学术论文 → 构建本地知识图谱 → 制作视频专栏的开源 skill。

Automatically discover papers (OpenAlex / arXiv), build a local knowledge
graph (课题组 / 作者 / 论文 / 论点 / 论据), rank strong research groups by
citation relations, render highlighted global & local graph views, and
produce a daily Bilibili video column episode (EasySlides deck + TTS
narration + gated release pipeline).

## 专栏流程 / Column flow

```
每日定时 ─ fetch_openalex / fetch_arxiv ─ build_graph ─ rank_groups ─ column_report
                                                        │
              ┌─────────────────────────────────────────┘
              ▼
   render_graph (global 全局格局 + local 论文地位高亮)
              ▼
   E:\bili\Bili 视频管线（EasySlides deck · IndexTTS2 配音 · Remotion 渲染 · 发布闸门）
              ▼
   episodes.json 记录 ─ LESSONS.md 经验回写 ─ git commit & push（skill 自我进化）
```

## Quick start

```bash
git clone https://github.com/mappedinfo/paper-radar
cd paper-radar
python scripts/fetch_openalex.py --channel reinforcement-learning
python scripts/fetch_arxiv.py     --channel reinforcement-learning
python scripts/build_graph.py     --channel reinforcement-learning
python scripts/rank_groups.py     --channel reinforcement-learning
python scripts/column_report.py   --channel reinforcement-learning
python scripts/render_graph.py    --channel reinforcement-learning --mode global
```

Python ≥ 3.10, standard library only (no pip installs needed for the radar
itself). Reports land in `reports/`, graphs in `data/<channel>/graph.json`,
renders in `data/<channel>/renders/`.

## 新建一个专栏频道 / Add a channel

Copy `channels/reinforcement-learning.json`, adjust topic queries, venue
whitelist, and seed groups, then run the same commands with `--channel <id>`.

## Docs

- Skill routing: `SKILL.md`
- Graph schema: `references/graph-schema.md`
- Daily runbook + skill-evolution protocol: `workflows/daily-column.md`

## License

MIT © mappedinfo
