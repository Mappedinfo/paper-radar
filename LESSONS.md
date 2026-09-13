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

## 2026-09-13 (第一期双片自动生产)
- 全自动首跑成功：Bellman 可塑性论文全管线（arXiv 回退抓取→12 场景→SVG deck→IndexTTS2→ffmpeg 合成→预检→自动上传 BV1k6Yi64EuD）；T1 视频同管线进行中。
- generate:index-tts 的收尾步骤读 deck/deck.json，务必先跑 deck:build 再跑 TTS，否则装配步骤崩溃（本期首片踩坑后手动装配，第二片调整顺序后自然通过）。
- release:check 为 PlainDeck 硬编码：paper-radar 管线需 deck:build 生成合规 deck.json（作为可编辑副产物）、references.md、manifest 补 consent_record（注意 heredoc 会把  转义成垂直制表符，路径用正斜杠）与 slide_count=场景数。
- ffmpeg concat 清单必须写绝对路径；输出时长用 -t 锁定到配音时长，否则尾帧多出约 2.5 秒。
- prose 黑话表禁「赋能」，empowerment 一律用英文术语；「对齐」也是黑话，TITO 叙述改用「一致/回放」。
- paper-fetch CLI 已从 Rimagination/paper-fetch-skill 源码安装（lite 模式）；对 2026-09 新 arXiv 条目解析 ambiguous，疑似缺浏览器组件的降级，待装 playwright 后复测。
- 图谱上游补充：empowerment 谱系（Klyubin 2005 / Leibfried 2019 / Dohare 2024 Nature）不在抓取正则覆盖内，已手动补节点与 cites 边——标题正则后续应加 empowerment/inverse RL 等术语。
- 全局图英文机构名按字符截断有断词问题，待按词边界换行。

## 2026-09-13 (设计 v2 · EasySlides 规范)
- 创作者反馈：context.setup「为什么是这一页」与 context.implication「这一页带来什么」改为创作辅助信息，不再渲染上片；PPT 设计遵循 easyslides/references/design-guidelines.md（学术蓝 #003366/#0066CC/#CC0000、60-30-10、页眉-关键信息条-内容区-页脚、CJK 字号阶梯）。
- make_deck_svg.py 全面改版为浅色学术风；关键信息条累积句至 ≥24 字、最多两行；图谱页作为带边框图嵌入浅色页面。第一期（Bellman）为旧深色版，第二期（T1）起用 v2。
- 今日双片全部自动推送成功：BV1k6Yi64EuD（Bellman 可塑性）、BV13wYq6VE7j（T1 终端智能体）。
