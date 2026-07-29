# 100x Learning

100x Learning 是一个面向 Codex 的学习 Skill。它把长材料或陌生主题整理成当前真正需要理解和使用的知识，并可继续支持研究、概念讲解、案例分析、决策、实践和写作。

## 能做什么

- 从字幕、文章、课程、访谈或书摘中找出高价值片段。
- 从视频、书籍和长文中筛选适合普通受众分享的内容，整理核心主张、必要语境、支撑材料、来源状态和可用素材，供后续写作或媒体制作使用。
- 把已经整理和核实的内容写成能够独立成立的短帖、Thread 和短文案；指定平台或要求多条内容时，先建立结构化分发计划，保证各条内容使用明确且不同的任务、角度、证据和互动方式。
- 研究陌生主题，判断来源质量，整理关键证据、反例和适用边界。
- 拆解概念、机制及相近概念之间真正影响理解的差异。
- 把学到的内容用于模拟、分析、决策、工具、方案或文章。
- 根据已有样稿和明确偏好辅助起草、修改及分析作者声音。
- 起草和修改独立短内容、文章或 Newsletter 时，把内容真源、当前作者声音、对应写作模板和同类型完整案例同时交给当前 Agent；多轮修改以当前正文和仍然有效的要求为唯一真源。
- 在获得写入授权后，把稳定的新认识合并进本地知识库。

它不用于具体媒体载体选择与制作、单纯翻译、格式清洗、无学习目的的普通摘要、泛泛的打卡计划或与学习无关的普通代写。图文卡片、GIF、视频、音频和播客由独立的 `visual-multimedia` Skill 负责。

## 使用方式

将本仓库作为 Codex 可发现的 Skill 目录加载，确保 `SKILL.md` 位于目录根部。随后可以直接用自然语言提出任务，例如：

```text
帮我通读这份课程字幕，找出最值得学习的片段，并说明取舍。

研究一下间隔效应。我想判断它怎样用于技术学习，请优先找一手来源。

把“机会成本”讲清楚，再用我现在的项目选择做一次分析。

根据这些实践记录整理一篇文章，先保留我的真实经历和判断。
```

需要把研究直接变成可继续修改的文章文件时，可以使用简短指令：

```text
文章模式：把这次项目复盘写成文章
```

`文章模式` 默认先检索相关旧文、项目和文章归档，只把当前用户原文、用户确认稿或已发布文章作为作者材料，再研究成文必需的缺口。大纲、参考正文和未确认草稿保存在 `30-Projects`；用户确认稿或已发布文章才进入 `40-Outputs`。

## 内容写作

独立短帖、Thread、短文案、文章和 Newsletter 由当前 Agent 直接起草和修改。每次成文都从用户本轮原话、当前有效正文、确认稿、已发布内容或声音档案中取得作者声音，再同时读取对应模板和同类型完整案例。模板负责内容职责，案例展示开头、推进、密度、节奏和收束，内容真源负责事实，作者材料负责用词、句长、重复、判断力度、幽默和自然毛边。用户明确要求病毒式传播时，在正文案例之外再读取开头案例。平台化或多条短内容另外生成并校验唯一 `distribution_plan`。卡片内文字、口播、字幕和其它与媒体成品共同设计的文字仍由 `visual-multimedia` 负责。

用户只要求判断 AI 味或模板感时，流程引用具体原句、命名可观察模式并给出最小修法；用户同时要求改写时才进入最小有效编辑。详细边界与验收方式见 [`references/content-writing.md`](references/content-writing.md) 和 [`references/content-audit.md`](references/content-audit.md)。外部模型只在用户本轮明确点名时使用。

具体触发条件、任务流程和行为约束以 [`SKILL.md`](SKILL.md) 为唯一运行规则。README 只提供面向使用者和维护者的项目说明。

## 本地知识库

Skill 可以读取项目根目录下的 `System Knowledge`，但该目录属于个人知识库，不随仓库分发，也不会被 Git 跟踪。

- 存在 `System Knowledge/Home.md` 时，Skill 按其中的目录和文档约定检索已有知识。
- 目录不存在时，Skill 会跳过本地检索并继续当前任务，不会自行猜测路径或创建另一套知识库。
- 读取知识库不代表获得写入权限；只有用户明确授权后才能写入。

## 项目结构

```text
100x-learning/
├── SKILL.md             # Skill 的唯一运行入口和规则来源
├── references/          # 各任务流程的详细规则
│   ├── shareable-content-selection.md
│   │                     # 分享候选识别与内容真源交接规则
│   └── social-content-distribution.md
│                         # 平台内容组合和 distribution_plan 规则
├── harness/             # 确定性校验工具
├── tests/               # Harness、分发结构和字幕工具的单元测试
├── scripts/
│   └── normalize_subtitles.py
│                         # SRT、VTT 和时间戳文本规范化工具
└── System Knowledge/    # 可选的本地个人知识库，不纳入版本管理
```

## 开发与验证

项目使用 Python 3.10 或更高版本，当前不需要安装第三方依赖。在仓库根目录运行：

```powershell
python -m harness doctor
python -m unittest discover -s tests -v
```

`doctor` 会检查：

- `SKILL.md` 及其 frontmatter 是否存在。
- `SKILL.md` 引用的本地资源是否存在。
- 可选的本地知识库入口是否可用。

Harness 的其他子命令用于校验任务合同、研究证据、写作输入、平台内容分发计划、内容审计和知识库文档。运行下面的命令可以查看完整列表：

```powershell
python -m harness --help
```

## 字幕规范化

`scripts/normalize_subtitles.py` 可以读取 SRT、VTT、带时间戳的文本或普通文本，清理标签与重复字幕，并输出 Markdown 或 JSON。它不会编造缺失的时间信息。

```powershell
python scripts/normalize_subtitles.py input.srt > normalized.md
python scripts/normalize_subtitles.py input.vtt --format json > normalized.json
```

可用参数：

```powershell
python scripts/normalize_subtitles.py --help
```

## 维护约定

- 运行行为只在 `SKILL.md` 中定义；README 不复制完整提示词和流程规则。
- 详细方法放在 `references/`，并由 `SKILL.md` 明确引用。
- 行为变更在当前任务中用至少两个表面不同的普通请求做临时跨场景推演，不把提示词、回答或评估报告保存进仓库。
- 长期测试只检查结构、合同字段和不依赖具体案例措辞的明确不变量。
- `System Knowledge` 只保存个人知识，不作为仓库运行的必要依赖。
