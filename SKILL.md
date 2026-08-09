---
name: 100x-learning
description: 帮助用户读懂材料、研究主题、解释概念、把知识用于真实问题，并直接写成短帖、GitHub 项目介绍或文章；也能接入视频和社交来源，筛选分享内容，根据发布反馈继续选题和改进内容，以及初始化、检查和维护本机私人知识库、内容案例、钩子与写作记忆。适用于划重点、系统学习、分轮处理长材料、内容审查、宣发写作和知识沉淀；媒体制作、普通翻译、广告投放、销售页、邮件营销、品牌全案、完整营销策略和实际发布使用对应的专门流程。
---

# 100x Learning

## 目标

把材料、陌生主题或真实问题变成用户现在能理解、判断、使用或分享的结果。资料已经足够时停止，不把简单任务扩成研究项目，也不把写作任务改造成流程审计。

普通解释、研究结果、清单、内容审查和可发布文字直接完成；适合一次复制的成品在当前回复交付，较长、结构复杂或需要继续修改的文字使用临时 Markdown 文件。用户明确要求保存、更新或沉淀时才写入长期位置。媒体制作、上传和发布分别由用户明确要求触发；图文卡片、GIF、视频、音频和播客交给 `visual-multimedia`。

## 核心原则

1. **先完成用户真正要的结果。** 直接理解用户的自然语言要求并完成相应内容。同一请求包含研究、写作或保存等多个明确结果时依次完成；用户只要其中一项时，在该结果完成后停止。
2. **写作默认发现新材料。** 新写、扩写、改写和实质重组按 `references/prewriting-research.md` 搜索能补充现有内容或增强传播力的真实材料。用户明确禁止联网、要求只使用给定材料，或只改错字、格式和等义措辞时不搜索。
3. **写作案例和开头钩子帮助表达。** 正常写作读取有帮助的参考写作案例和参考开头钩子，并打开相应完整原文；私人库或参考不可用时继续写作。
4. **相信模型的创作判断。** 给模型真实材料、完整参考、用户硬要求和少量必要边界后，由它决定角度、取舍、结构、语言、篇幅和结束位置。

## 根据请求使用材料

下面的说明可以同时参与同一请求，只提供完成工作所需的材料和方法，不建立互斥路线：

- 判断学习方法读取 `references/learning-process-and-method-selection.md`；理解材料与筛选片段读取 `references/material-analysis.md`，需要筛选可分享内容时再使用 `references/shareable-content-selection.md`。
- 研究主题、比较来源或核查重要事实读取 `references/research-context-reuse.md` 和 `references/research-led-learning.md`；解释概念读取 `references/concept-deconstruction.md`；系统学习读取 `references/continuous-learning.md`。
- 把知识用于真实问题读取 `references/practice-led-learning.md`；建立长期内容方向读取 `references/content-strategy-and-topic-selection.md`；复盘已发布内容读取 `references/published-content-review.md`。
- 视频、社交帖子和 Thread 先按 `references/source-ingestion.md` 取得可靠正文与上下文，再直接用于用户要的结果。
- 可发布文字共同使用 `references/prewriting-research.md` 和 `references/content-writing.md`。单个 GitHub 项目可补充 `references/github-project-short-content.md`，GitHub 项目清单可补充 `references/github-project-list.md`，文章和 Newsletter 可补充 `references/article-from-practice.md`。
- 审查内容读取 `references/content-audit.md`；用户要求检查或清理 AI 味时同时读取 `references/natural-writing.md`。正文需要福利、时限、行动入口或披露时补充 `references/publication-requirements.md`。
- 私人知识库的初始化和接入读取 `references/private-knowledge-library.md`；知识写入读取 `references/knowledge-base-workflow.md`；库健康检查读取 `references/knowledge-base-health.md`；批量接入读取 `references/bulk-knowledge-ingestion.md`；需要跨任务恢复时读取 `references/durable-learning-projects.md`。
- 用户要求维护完整案例或钩子时分别读取 `references/content-case-library.md` 和 `references/hook-library.md`；作者声音、发布历史和内容查重使用 `references/personal-writing-memory.md`。

用户只点名本 Skill 或只附材料而没有指定产物时，直接讲清材料本身。直接回复和可发布文字默认使用中文；只有没有清楚中文说法、读者需要按原名搜索或操作，或者用户要求官方写法时才保留必要外文。普通一次性结果不增加持久化；只有用户明确要求保存、更新或沉淀时才写入长期位置。

## 写作

### 准备并直接成文

根据用户要求直接处理本次成品。连续反馈只改变用户本次纠正的方面，不把上一对象的事实、原句和一次性结构带到新对象。

按 `references/prewriting-research.md` 搜索和净化材料。写作规则只从 `references/content-writing.md` 原样取得。

运行 `python scripts/private_library.py show` 取得私人库根目录。短帖和 Thread 从社交内容案例索引、文章和 Newsletter 从文章案例索引打开有帮助的完整案例；所有成品从同一份钩子索引打开有帮助的参考开头钩子。私人库或参考不可用时直接继续写作。

参考写作案例和参考开头钩子必须来自不同文件，完整原文也不能相同；缺少可区分的另一份参考时保持缺省并继续写作，不让同一内容同时充当两种参考。

短内容默认不读取作者声音，用户明确要求“像我写”或提供声音样稿时再使用。文章和 Newsletter 默认读取现有可用的长期作者声音与可靠样本；没有时继续写，不校验、不停止。任何来源材料都不会因为使用第一人称而自动成为用户声音。

单个 GitHub 项目、项目清单、文章、Newsletter 和包含发布事实的内容可以同时读取上面列出的专项说明。

按 `references/content-writing.md` 把用户明确提出的写作要求、写作规则、净化后材料、参考写作案例、参考开头钩子和其它实际写作输入组成当前请求的写作输入，完整读取后直接成文，材料准备和成文在同一次回复中连续完成。写作要求能直接摘录用户原话时不改写，不加入材料数量、预选重点、身份说明、篇幅判断或覆盖范围。参考案例与钩子只使用实际正文，去掉案例库和钩子库生成的标题、栏目名与存储元数据；其它写作输入也不带来源名称、原始材料文件名、路径或链接。

用户明确要求多个候选时完整交付相应数量；没有指定数量时只生成一个。候选不自动评审、融合或润色。

### 交付

每次写作在同一次回复中固定展示四部分：

1. **写作要求**：只放用户本次明确提出的要求；能直接摘录时不改写，也不加入系统推断。
2. **写作准备材料**：在独立代码块中完整展示本次实际使用的写作输入，不另建临时文件，也不重新摘要或改写内容。
3. **结果**：每个完整成品分别放在独立代码块中；较长或需要继续修改时可以另存临时 Markdown，并在代码块后提供可点击链接。
4. **本次创作参考**：只列出本次实际读取的案例与钩子名称，不显示文件名、路径、原始材料来源、采用说明、评分或隐藏推理；没有读取时直接写“本次未使用额外案例与钩子”。

## 知识库与持久化

私人知识库独立于 Skill 源码。初始化、接入、读取或写入前先读 `references/private-knowledge-library.md`，由 `scripts/private_library.py` 返回本次唯一根目录；知识、案例、钩子和写作记忆都从这里定位，不根据当前仓库或客户端目录猜测位置。

普通解释、预览稿、短成品和临时 Markdown 只服务当前任务。用户明确要求保存、更新或沉淀时，取得私人库根目录后按 `references/knowledge-base-workflow.md` 找到唯一正式位置：同一主题更新现有文档，确实是独立主题时才新建。私人库已经配置 Marktree CLI 时，正文和索引统一经过 `scripts/marktree_integration.py` 写入；知识应放在哪里仍由本 Skill 与 `Home.md` 决定。

用户明确要求根据给定材料沉淀时，先完成材料理解，再按材料实际作用写入：需要长期保留的原始材料进入 `20-Sources`；稳定概念、机制、结论和边界合并到 `10-Knowledge` 的对应主题；材料本身是完整成品且具有创作参考价值时才进入完整案例。只有用户明确要求保存一段原始开头时，才由独立入口写入钩子库；案例导入不会派生钩子。写后重新读取正式文件并运行相应索引检查，告诉用户实际更新了什么。

发布历史和写作风格样本使用 `scripts/writing_memory.py` 的两个入口：`voice` 只读取明确允许用于学习用户写法的同类作品，`novelty` 只判断主题是否重复。用户确认、保存或更新最终作品后，按 `references/personal-writing-memory.md` 更新索引。

长期内容方向与写作风格分别保存在 `60-Systems/Writing/content-strategy.md` 和 `60-Systems/Writing/style-guide/voice.md`。持续选题只在真实内容项目的 `30-Projects/Content/<系列>/topic-portfolio.md` 保存决策状态；已发布内容复盘链接最终正文和真实反馈，不复制正文。一次结果保持为假设，只有重复证据、直接行为证据或用户确认支持的认识才进入对应的长期文件，发布表现本身不改写用户声音。

用户明确要求保存或更新完整案例时，使用 `scripts/content_case_library.py add-case` 写入完整社交内容或文章案例；短帖和 Thread 都使用 `social`，文章使用 `article`。用户明确要求保存或更新钩子时，使用 `scripts/hook_library.py add-hook` 写入不区分成品形式的独立钩子库。两个入口写后都运行各自的 `build-index` 和 `validate`，没有互相转换或引用的参数。

本地 SRT、VTT、带时间戳 TXT 或断行严重的字幕需要规范化时，使用 `scripts/normalize_subtitles.py`，保留原文件和真实时间位置。

个人写作记忆只提供经过确认的写作风格样本与发布历史；内容案例库只提供创作参考，两者不能替代当前对象的事实和明确要求。普通翻译、转写、格式清洗和普通计划走对应专门流程；广告投放、销售页与落地页、邮件营销序列、品牌全案、完整营销策略和实际发布不属于本 Skill 的文字写作结果。

## 交付前检查

- 成品直接回答用户要求；资料足够时已经停止。
- 用户指定的重点、材料关系、数量、语言、格式和权限保持不变。
- 写作输入使用 `references/content-writing.md` 中唯一的模板和写作规则；材料准备完成后已经在同一次回复中直接成文。
- 普通写作没有因私人库、案例或钩子不可用而停止；长期保存、发布和其它外部动作只在用户明确要求时执行。
