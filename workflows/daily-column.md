# Daily column runbook (daily 定时例程)

Run order (all from the skill root, ~2–4 min):

```bash
python scripts/fetch_openalex.py --channel reinforcement-learning
python scripts/fetch_arxiv.py     --channel reinforcement-learning
python scripts/build_graph.py     --channel reinforcement-learning
python scripts/rank_groups.py     --channel reinforcement-learning
python scripts/column_report.py   --channel reinforcement-learning
```

## 1. Read the report

`reports/reinforcement-learning-<date>.md`. Check the 今日候选 list.
If the top candidate is weak (no clear story, or below score 0.35), skip the
episode and only keep the graph updated — say so in the report.

## 2. Render the graph views for the episode

```bash
python scripts/render_graph.py --channel reinforcement-learning --mode global
python scripts/render_graph.py --channel reinforcement-learning --mode local \
  --focus "<chosen paper_id>" --hops 2
```

Convert SVGs to PNG (easyslides venv has cairosvg; else use PowerPoint or
any converter) — these become the opening slides of the episode.

## 3. Produce the episode video (E:\bili\Bili pipeline)

1. Register the project under `E:\bili\Bili\projects\<slug>/` with
   `sources.json` and `storyboard.json`. Full text **and paper figures** are
   fetched with the **paper-fetch skill** (`~/.qoder/skills/paper-fetch-skill`)
   — 保存决策在本例程中固定为：保存到 `E:\bili\Bili\projects\<slug>\`、
   `--asset-profile body`（下载正文图表，供解读引用）：

   ```bash
   paper-fetch --query "<doi-or-title>" --output-dir "E:\bili\Bili\projects\<slug>" \
     --format markdown --save-markdown --asset-profile body
   ```

   If the paper-fetch CLI / MCP is unavailable, fall back to downloading the
   arXiv HTML full text (`https://arxiv.org/html/<id>`) into
   `projects/<slug>/paper.html` and extracting figures from the official TeX
   source / PDF. `evidence_level` must reach `full_text` before narration.

   **论文图表使用政策（2026-09-13 更正）**：解读视频允许使用论文图表
   （正常解读引用）。使用时必须遵守 E:\bili\Bili 的
   `references/original-visual-contract.md`：
   - 图表只用于有解读指向的证据展示，不作为装饰；
   - 幻灯片上带可见的论文来源与页码标注；
   - 每个衍生文件记入项目 `visual-assets.json` 台账（来源、变换、哈希）；
   - 提交前的版权声明与人工确认闸门保持不变。
2. Episode structure (13–15 scenes):
   - scenes 1–3: 图谱定位 — global view (领域格局), local view (论文在组内与
     引用网络中的位置, 用高亮), 该课题组实力榜数据;
   - middle scenes: paper 解读 as usual (hook/context/method/evidence/limits);
   - closing: 图谱回看 (这篇论文将如何改变引用网络).
   Graph numbers spoken on screen (被引次数、排名、组内论文数) must come
   from the graph store, and every paper claim from the full text.
3. Build the deck with **EasySlides** (`~/.qoder/skills/easyslides`), embedding
   the rendered graph SVG/PNG pages; export per its SKILL.md. The deck→video
   composition path may fall back to the validated PlainDeck renderer if the
   EasySlides export path is not wired yet — record which one was used.
4. Narration: `npm run generate:index-tts -- ../projects/<slug> --device cuda`
   (shiqi profile), then `render:project`, `release:check` — all gates
   unchanged (`check:narration-prose`, density, traceability, preflight).
5. **No upload.** Upload/publish stays behind the human gates. Record the
   episode in `data/<channel>/episodes.json`:
   `{"date", "paper_id", "slug", "bvid": null, "status": "release_ready"}`.

## 4. Skill evolution (每次制作后自动更新并推送)

1. Append to `LESSONS.md`: what worked, what failed, concrete script/config
   fixes applied today (one dated bullet list).
2. Apply the same fixes to the scripts/config immediately.
3. Commit and push:

```bash
git add -A && git commit -m "daily: <date> column run + skill evolution" && git push
```

If push fails (credentials/network), keep the local commit and surface the
error; never rewrite history to work around auth.

## Cost guards

- One episode per day maximum; a full production (TTS + render) costs
  ~20 GPU-minutes — skip if the candidate is weak.
- Raw snapshots accumulate daily; keep only the last 14 days
  (`raw/` files older than 14 days may be pruned; the graph keeps everything).
