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

## 2026-09-17 (每日例程第 5 次自动运行)
- 双片完成：GrowMTP（BV1kveK6GEBD，11 场景 260.79s，RL 循环内自养草稿头，8 图入片+手工指定价值曲线图）与 ImpossibleRubrics（BV1CveK6GEKX，11 场景 257.19s，评分标准压力测试基准，4 图入片）。
- OpenAlex 连续第 4 天 503/504；arXiv API 稳定，图谱 168 篇/956 作者。fetch_openalex 建议加连续失败计数静默降级（连续≥3 天跳过重试，只记一行）。
- 单次上传防护连续第 3 天生效（两期 submissions==1）。
- TTS 完成判定全面改为磁盘产物法（narration.wav 存在 + scene wav 数 == 场景数），不再依赖日志行，避免缓冲误判。
- GrowMTP 自动分配只命中 1 图，价值曲线主图（fig-01）按 LESSONS 手工指定到证据页——自动分类对「无 results 关键词的主结果图」仍弱，后续可在 caption 加权重规则。

## 2026-09-21 (漏跑 4 天的事故审查与修复)
- 事故：09-18 至 09-21 连续 4 天未执行。根因确认为创作者判断——ZCode 桌面端未运行时，应用内定时任务不触发，且错过的槽位不补跑（CronList 证据：lastRunAt=09-17 08:00:16，nextRunAt 直接跳到 09-22 08:00）。
- 修复①（系统层）：Windows 任务计划程序注册「ZCode AutoStart for Paper Radar」，每日 07:55 启动 C:\Program Files\ZCode\ZCode.exe，含 WakeToRun（睡眠唤醒）与 StartWhenAvailable（错过后开机即补启动）。
- 修复②（应用层）：08:00 例程指令加入 last-daily-run.txt 标记文件读写——开跑前检查防重复，成功后写入日期。午间 12:30 备份触发的 CronCreate 因「定时任务会话内不可再建任务」失败，待创作者在普通会话中补建。
- 追加经验：图像生成类论文的附录 held-out 图会把 extract_figures 抽到 50+ 张（λ-GRPO 抽了 53 张），台账照记但只正文图入片；正文引用图谱统计数字（234 篇等）需在 sources.json 声明「知识图谱统计」claim 才能过溯源门。
- 今日补跑双片：CodeMidas（BV1Vuh667EE7，10 场景 246.57s）与 λ-Controlled GRPO（BV1Guh667EJY，10 场景 253.24s），OpenAlex 恢复后图谱扩到 234 篇/1266 作者。

## 2026-09-22 (设计 v4 · 接入花叔 huashu-slides 设计体系)
- 创作者判定 v3.2 版面「太差」，指定参考 alchaincyf/huashu-skills（已克隆到 ~/.qoder/skills/huashu-skills-repo）。
- 诊断 v3.2 差距：标题多为短语而非断言句（Assertion-Evidence）；字阶不够大（标题 22pt vs 花叔 ≥36pt）；正文段落太长（一页一论点被破坏）；指标卡平铺缺视觉锚点；英文 section label 未作为设计元素。
- v4 落地（Pentagram Editorial 编辑杂志风 + Fathom 数据叙事锚点，均选自花叔「技术分享/数据报告」第一推荐）：断言式大标题 40pt 两行封顶；kicker 行（章节中文+英文 label）；正文改为 lead 首句 18pt + 尾注最多 4 行、放不下自动截断进备注；指标页加 hero number（首指标 60pt 橙红锚点）；左侧 0.14in 藏青书脊；章节进度改为 8 点圆点；引言块改 serif 大引号；overlap 审计门保留并通过。
- body() 的自适应规则：y > 6.60in 直接不上正文（内容进备注），否则按剩余空间截断行数加省略号。
- 花叔的两条通用经验同步进流程认知：一是「插画/漫画风格 AI 生成远好于极简风格」，本栏目坚持 Pentagram 编辑风属例外（学术严肃性优先）；二是 Path A（HTML→PPTX）与其原生形状思路等价，我们保留 python-pptx 原生构建（可编辑性同等级）。

## 2026-09-22 (每日例程 · v4 设计体系首跑)
- 双片完成且为首日 v4（花叔 huashu-slides 体系）：SynthDemo-RL（BV1bkhC6HEX3，10 场景 216.68s，具身零奖励屏障）与 Deep-BQRL（BV1UkhC6HEmq，10 场景 268.86s，缓冲分位数上神经网络）。
- v4 首跑体感：断言标题 + hero number 在证据页效果显著；prose 门新拦截「不只是…也」「不是…而是」跨句变体（前者为「不只(?:是)?…还/也」正则命中但出现在无「还/也」收尾的句式，实际是误报边缘——本轮按规则改写规避）；图谱统计 claim 模板已固化进例程指令。
- OpenAlex 连续第 5 天 503；arXiv API 429 一次后重试成功（重试机制生效）。
- 单次上传防护连续第 5 天生效。

## 2026-09-22 (v5 · 接入去AI味与稿件分发两个花叔 skill)
- 创作者指定新增两个能力并升级 v5：①tramstop-skill（重装备，四层AI味模型+经验注入，已克隆 ~/.qoder/skills/tramstop-skill-repo）与内置 huashu-proofreading（轻量三遍审校）用于文章去AI味；②dukou（渡口，Chrome 插件+本地桥 127.0.0.1:8787，已克隆 ~/.qoder/skills/dukou-repo）用于稿件分发到 X Articles / B站专栏 / 公众号排版器。
- tramstop 核心洞见进流程认知：AI味分四层（词汇<句式<结构<经验），词汇句式两层已被 human-writing prose 门覆盖，深度两层新增 scripts/deai_narration.py 做报告（结构层：导游路标/金句收束/回扣升华；经验层：两头堵/模糊量词/无专名无数字的可替换细节），排布按权重 experience≥structure；只报告不改稿，改写在 storyboard 完成后重跑 prose 门与报告直至清零。白熊隔离原则：诊断与改写分开，坏例清单不进成稿阶段。
- dukou 集成点：例程第 4 步后新增（可选）——narration-script.md 轻改写为专栏文章后 `node dukou.js send <md> --dest bili --autofill`（B站专栏全自动）；`--dest x --autofill` 需用户点 Write；`--dest editor` 灌公众号排版器。填充后的发布/复制永远留给用户。Windows 下桥日志路径问题（脚本硬编码 /tmp）待上游修复，ping 前先 set TMP。
- huashu-proofreading 定位为轻量备选：口播稿走 tramstop 深检（已是 prose 门超集），公众号长文用 proofreading 三遍法（内容→风格→节奏）足够。
- v5 例程顺序：三门 → de-AI 报告清零 → （若分发）轻改写+dukou send。

## 2026-09-22 (v5.5 · 接入 huashu-report 报告纪律)
- 创作者指定接入 huashu-report（机构级研究报告 skill，已克隆 ~/.qoder/skills/huashu-report-repo），定位明确：我们虽不写论文，但做论文精读 = 科普型研究报告（读者无背景、理解领域并行动）。
- 融合点：四角色映射到既有流水线（sources.json=数据表、图谱场景=文献定位、v4 设计系统=信息设计师、对照表=可视化师）；新增硬规矩三条——每个数字带分母（百分比必须携 N 上片）、图注写结论、局限场景升级为替代解释式（可能被什么推翻、排除了哪些、剩哪些没排除）；过程自述禁令扩展到正文。页数契约改为 15 页封顶（封面 1 + 场景 13-14）。
- huashu-report 的「工作顺序不能颠倒」（定一句话→数据表→正文→机制与文献定位→图→逐页自检）验证了我们 sources.json 先于 storyboard 的既有顺序，机制定位靠图谱场景承担。

## 2026-09-22 (v5.5 首期 · RAVEL 论文精读)
- 首期按 v5.5 报告纪律制作并推送（BV1C5hC66EQ9，11 场景 259.93s，12 页在 15 页契约内，7 图入片 3 张自动分配）。
- 报告纪律首跑体感：①「每个数字带分母」在 storyboard 写作阶段直接生效（73.73 带五轮、+5.79 带基线名）；②局限场景升级为替代解释式（算力解释被同预算对照压住、任务域单一与冗长回答未排除），表述更硬；③de-AI 报告在改稿时用了两次（先闭环→回路的黑话替换，再清路标），确认「诊断与改写分离」必要。
- prose 门新发现黑话词「闭环」，与「赋能/对齐」同列，回路为通过词；后续写稿直接用回路。
- 首次单日三片（例程双片 + 本期 v5.5 首跑），单次上传防护 3/3 生效。

## 2026-09-22 (v4.3 · 换行与密度双修)
- **换行 bug 根因是边距不是测量**：python-pptx 文本框默认左右边距 0.1in，PIL 按全宽测出的"安全"行在 PowerPoint 里实际可用宽度少 0.2in，被二次换行成孤字断行（中文孤字、英文拦腰）。修复三件套：`margin_left/right=0` 归零、`SAFETY=0.97` 保守测量、`_ASCII_WORD` 英文按词整体换行。交付前另跑整行硬溢出校验（实宽>框宽即败），本次 12 页 0 溢出。
- **密度问题的两层根因**：字阶（14pt 灰色正文+4 行硬帽）只是表层；深层是 storyboard 的 `context.setup/implication` 两句写了从不渲染、body 又被"一页一论点"削成一句话。v4.3：34/18/16/15pt 字阶、正文墨色动态填充到页脚预留线、context 两句以辅助色+橙红短线渲染上片。无全局字数硬帽，密度由版心空间决定。
- **黑话从标题漏进片里的路径已封死**：prose 门此前只查 narration，`check:narration-prose` 现在每场景多查一项 slide text（heading+body+context 两句）——本次它当场拦下我新写句子里的「不只…还…」翻案句，门的自证。
- **图注三处卫生**：PDF 断词连字（`in- teraction`）在 extract_figures 去连字；超长截断走词边界+省略号（`[:200]` 字符切片产生过 `enviro` 半截词）；图注改为审计对象且高度实测推进（固定 0.32in 推进曾让两行图注压图 0.22in，审计打开后当场暴露 3 页）。
- **教训：给"应该不会重叠"的组合留审计开关**。图注原本 kind=frame 不进 overlap 检查，改成 kind=text 后立即抓出 3 处真实压图。相邻元素的间距若靠固定常数而非实测高度，迟早压上。
- **视觉模型读图会复述旧内容**：同路径同名 PNG 二次上传 CDN，视觉分析返回了上一版的画面（stale）。验证渲染结果要么用新文件名，要么用 PPTX XML/几何数据做 ground truth。
