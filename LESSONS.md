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

## 2026-09-13 (v3.2 · 论文原图管线 + 实测布局 + overlap 审计门)
- 创作者要求：论文原图（架构图/核心结果图）自动裁剪入 PPT 并自动解说。extract_figures.py 重写为 PDF 截图路线（创作者建议）：下载 arXiv PDF → 题注文本块（Figure N）锚定 → 上方图像/矢量聚类区域 → 2.5x 裁剪；剔除与正文文本块重叠>35%的区域（flash 视觉质检反馈）；题注关键词分类（results 词优先于 architecture 词）；architecture→方法页、results→实验页自动分配；visual-assets.json 台账自动登记。
- build_pptx：论文原图优先于自制指标表（同页只取论文图）；图注带「论文 Figure N，第 P 页」出处；备注页自动前缀「本页图示（论文 Figure N）…caption」解说。
- overlap 自动计算（创作者问「有什么逻辑自动计算 overlap 吗」）：v3.1 只有字数估行高+WARN，中英混排实际换行与估算有偏差导致第 4/5 页溢出。v3.2 改为 PIL+微软雅黑真实字宽测量（measure_lines）精确计算每块高度，构建后 Audit 两两包围盒相交检测（>0.03in 阈值）+ 页脚越界检测，任何命中即构建失败——不再静默交付越界页。本轮 13 页审计全过。
- flash 视觉模型（mcp analyze_image）用于裁剪图质检可行：本地裁剪图经 Read 自动上 CDN 后可传入；本轮质检发现 fig-03 混入正文文字并反馈修复（文本区剔除规则）。
- PyMuPDF fitz API deprecated 警告：后续换 import pymupdf。

## 2026-09-14 (每日例程第 2 次自动运行)
- 上游故障：OpenAlex 503/504、arXiv API 429（网页端正常），两源重试无效；雷达沿用昨日图谱数据继续，选题池不受影响。教训：API 与网页端可用性要分开判断，fetch 前先 curl 探活。
- 双片 v3.2 全自动完成：信念分叉（BV1MfYr6SECA，13 场景 333.89s）与 G2QDR（BV18ZYr6nEuh，12 场景 284.13s），均为原生可编辑 PPTX→COM 导出帧→ffmpeg 合成，论文原图 6+6 张入片，两片 overlap 审计通过、release 预检通过。
- ⚠️ 重复投稿事故：期 2 上传命令因进程替换写法 bug 被 eval 两次，产生重复稿 BV1uZYr6nEGR（已报告用户手动删除，保留 BV18ZYr6nEuh）；尝试的删除端点 404。教训（写入流程认知）：任何上传命令只允许单次 eval，执行后必须 grep download.log 校验 BV 数量与预期一致，多退少报。
- 两个 TTS 任务并发时资源锁自动交替（scene 级 FIFO），总时长与串行相当，可安全并行。
- extract_figures 新增防误判：正文里“Figure N shows…”不再当题注（CAP_RE 排除引用式句首），同号 figure 去重保首个；价值曲线等关键图可手工指定分配（storyboard.paper_figure 覆盖自动分配）。

## 2026-09-15 (每日例程第 3 次自动运行)
- 上游连续第二天故障（OpenAlex 503 / arXiv API 429，网页端正常）；雷达沿用图谱，选题池不受影响。连续两天说明非瞬时抖动，fetch 脚本后续可加「连续失败即静默跳过」降级，避免每日重试噪音。
- 双片全自动完成：TRACE（BV1iPe76AERy，10 场景 236.11s，广告诊断合成奖励，论文 2 图入片）与多步前瞻近优 RL（BV1rRej6uE88，11 场景 275.82s，纯理论无实验图，用定理要点表替代）。
- 昨日重复投稿教训生效：上传统一为单次 eval + 输出重定向 + grep 校验 submissions_this_run == 1，两期各恰好一次提交。
- export_pptx_png.py 固化为脚本（内联 python -c 的 bash 转义在 Windows Git Bash 下极易踩坑，不再内联）。
- 理论论文无图时的版面方案：evidence 页用「表 N ｜ 定理要点」metrics 表替代论文原图，题注注明依据定理编号。

## 2026-09-16 (每日例程第 4 次自动运行)
- arXiv API 恢复（60 条新论文入库，图谱扩到 152 篇/854 作者）；OpenAlex 连续第三天 504，考虑加静默降级。
- 双片完成：Fixed-SAE Track（BV11Pex6NEVE，11 场景 243.28s，RL 机制可解释性，10 图入片）与 BPO（BV1CPex6NESC，10 场景 224.60s，轨迹级策略优化，3 图入片）。
- 数字溯源门的归一化规则摸清：「N 个百分点」→百分比归一化；顿号连排的数字只有最后一个带单位。正文引用多个数字时必须逐个紧邻「个百分点/％」书写，claims 同步。已按此修复 BPO 的对照页。
- bash 内联 `&` 后台启动的进程在会话结束时被杀，且日志不可见；必须用 run_in_background 正式启动。BPO 首次静默启动失败后正式重启，靠 tts-scenes 断点续跑补齐，无重复合成。
- TTS 完成判定以磁盘产物为准（narration.wav + 全部 scene wav 的 mtime），日志行缓冲可能延迟刷出，轮询 grep 日志会误判未完成。
