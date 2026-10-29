# Daily column runbook (daily 定时例程)

Run order (all from the skill root, ~2–4 min):

```bash
python scripts/fetch_openalex.py --channel reinforcement-learning
python scripts/fetch_arxiv.py     --channel reinforcement-learning
python scripts/build_graph.py     --channel reinforcement-learning
python scripts/rank_groups.py     --channel reinforcement-learning
python scripts/column_report.py   --channel reinforcement-learning
python scripts/publish_site.py    --channel reinforcement-learning
```

The last step refreshes the GitHub Pages site (`docs/`) — it visualizes
relationships, 论点 and 论据 only, never paper content, and seeds claims
from produced episodes per `channels/*.json → episode_claims`.

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
3. Build the deck with **EasySlides** following `references/episode-deck-blueprint.md` (通用页面序列与布局契约：hook 第1页、图谱第2-3页、references 末页；context.setup/implication 不上片) (`~/.qoder/skills/easyslides`), embedding
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

## 5. Distribution hygiene & weekly review（B 站分发与周复盘）

Background (2026-10-29 复盘, reports/video-stats-2026-10-29.json): 70 期总播放
4643；播放呈三个平台期——正常期均值约 81（ep1-42）、恢复期均值约 115（ep49-58）、
两次坍缩期均值 4-7（ep43-48、ep59-70）。坍缩与内容质量无关（质量门同期不变），
判断为连续自动化投稿触发的分发限流。据此立规：

**投稿节奏（每次例程执行）**
1. 两期间隔 ≥60 分钟（第一期随例程投，第二期在 TTS/收尾后再投），不再连投。
2. 投稿时刻在 09:30 / 13:00 / 18:30 三档间按日轮换，避免固定时刻指纹。
3. 标题句式轮换（陈述式/问题式/数字式交替），tags 采用 3 个栏目固定词 + 2 个
   当期主题词，不再每期同一组；论文链接保持在简介尾部。
4. 每期投稿后在简介区保留一句论点总结（已由 publish.description 承担）。

**周复盘（每周日例程附带执行）**
1. 跑 `python scripts/fetch_bili_stats.py --channel reinforcement-learning`
   （view 端点；旧 archive/stat 端点已 404），写 reports/video-stats-<date>.json。
2. 看最近 6 期播放中位数：≥30 为正常；<20 视为限流信号，触发应对——
   次日改投单期、时刻换档、并在网页端搜论文标题抽查视频是否可被搜到
   （不可搜则连续 3 天只投单期）。
3. 内容配对结论（数据支持，保持）：每天「一期方法热词款（GRPO/RLVR/智能体等，
   拉播放）+ 一期理论深度款（Bellman/样本复杂度/机制设计，拉收藏）」。
   理论款互动率可达 13-38%，方法款播放进 TOP10 但互动率约 1-2%。
4. 系列串联继续：OPD/蒸馏系列包揽播放与收藏双榜（162 播放 12 收藏），
   多系列主题线在站点与口播中互链。

## Cost guards

- Two episodes per day maximum; a full production (TTS + render) costs
  ~20 GPU-minutes each — skip a weak candidate and do one instead.
- Raw snapshots accumulate daily; keep only the last 14 days
  (`raw/` files older than 14 days may be pruned; the graph keeps everything).
