# Lessons (skill evolution log)

每次专栏运行与视频制作后回写经验；同步修改脚本并推送。

## 2026-09-13 (init)
- 首次构建：OpenAlex + arXiv 抓取、图谱合并、课题组排名、SVG 全局/局部渲染、日报与选题打分。
- 视频管线沿用 E:ili\Bili 质量门（prose/密度/溯源/预检），deck 切换 EasySlides（见该仓库 AGENTS.md 决策）。
- arXiv Atom API 从本机访问不稳（429/超时）；fetch_arxiv.py 加重试并做 OpenAlex arXiv 索引兜底。
- OpenAlex 存在引用计数异常记录（如 2023 年论文 79075 被引）：plausible() 按年均被引 > 12000 剔除。
- default.search 主题漂移严重（阿尔茨海默/Grad-CAM 混入）：classic 与 recent 抓取和选题打分都加 RL 标题正则。
- 图内 cites 解析依赖 paper 节点记录 openalex 工作 id（oa 字段），缺失时引用边全丢——已修。
- 观察：近期桶（14 天 × 顶会白名单 × 标题匹配）天然很窄（1 篇），新论文主要靠 arXiv 源补充；后续可把窗口放宽到 30 天并加 PMLR 卷号匹配。
