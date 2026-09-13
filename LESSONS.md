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

## 2026-09-13 (设计 v3 · 学术化返工)
- 创作者批注：v2 太「新媒体卡片风」，不够学术；要求每页可见所处章节与原文出处、内容完整成句、字体成体系、零遮挡、解说词移入 PPT 备注。
- v3 落地：页眉双端信息（论文缩写｜§章节 · 作者年份）+ 八段章节进度带；论点框（thesis）+ 全量正文；指标卡改学术表格（表 N 题注+深蓝表头+斑马行）；公式显示块（式 N，serif 居中）；图表统一编号（图/表/式）；单一字族固定字阶（40 标题/27 论点/24 正文/22 表格/20 题注/18 脚注）两档字重；光标式排版按行计高、溢出自动降字号；narration 不再上片，经 build_pptx.py 写入每页 SPEAKER NOTES。
- build_pptx.py：python-pptx 全幅 PNG + notes（封面为栏目说明），产出 <slug>-deck.pptx 供批注/人工微调。
- 交付方式：先出 PPTX 批注版，确认后再进 TTS/合成/推送（本日视频 1/2 已按 v1/v2 产出并推送，v3 从下一期起生效，批注通过后可用 v3 重出旧片）。

## 2026-09-13 (v3.1 · 首轮人工批注闭环 + 原生可编辑 PPTX)
- 批注五条全部修复：封面英文按词边界换行（wrap_words）；页眉右=§章节·作者年份、页脚左=arXiv 编号（去除作者重复）；图谱页标题去口语改为直接命名（强化学习领域全局图谱/本期论文的局部引用网络，两期 storyboard 已同步）；背景页扩容并新增原生对偶示意图 diagram_mirror（动作⇄观察信息流，图 N 编号）；公式 20pt 加大加高。
- build_pptx.py 重写为原生构建：文本框/原生表格/自选图形，仅图谱为位图——PPTX 完全可人工二次编辑；PowerPoint COM 导出 PNG 已验证（deck/pptx-export/），人工改完的 PPTX 可直接导出 PNG 重出视频，PPTX 成为唯一视觉源。
- 批注解析注意：PowerPoint 365 批注存 modernComment_*.xml（ppt/comments/），经典 commentN.xml 解析抓不到；slide→批注映射走 slideN.xml.rels。
