---
name: content-system
description: 维护长期内容策略、持续选题、发布复盘、完整案例、独立钩子与写作记忆，并把真实内容和反馈用于下一轮决定。适用于筛选分享内容、规划长期方向、查重、分析作者声音和维护写作参考；不负责直接成文或私人知识库基础设施。
---

# Content System

## 目标

把材料、已发布内容和真实反馈变成可执行的内容选择，并维护以后会继续使用的内容策略、选题状态、完整案例、独立钩子和写作记忆。本 Skill 不写短帖或文章；重新创作使用 `$prep-this` 与 `$write-this`，已有成稿检查使用 `$clean-copy`。

长期状态保存在 `$private-knowledge` 管理的唯一私人库中。本 Skill 不另建配置、数据根或路径猜测，所有脚本从兄弟 Skill 的正式入口取得私人库。

## 取得材料和私人库

当前请求、用户提供的材料、实际发布正文、指标、评论和后续行动优先。需要私人库时运行：

```text
python <private-knowledge-skill>/scripts/private_library.py show
```

配置不存在时，当前回复能够完成的分享筛选、策略判断和发布复盘继续进行；只有用户明确要求保存、检索历史、维护案例或钩子时，才需要可用私人库。不会为了普通任务临时初始化。

## 分享选择、策略与发布复盘

- 从材料中选择值得分享的内容时读取 `references/shareable-content-selection.md`，先准确理解完整材料，再按当前受众和用途选择；它不替代正文写作或媒体制作。
- 用户明确要建立长期方向、持续选题或维护跨任务选题池时读取 `references/content-strategy-and-topic-selection.md`。
- 用户提供已发布正文、真实指标、评论或后续行动时读取 `references/published-content-review.md`，分开可观察结果、候选解释、其它解释和下一次验证。

一次结果默认在当前回复交付。只有用户明确要求保存或维护长期项目时，才把策略、选题状态或复盘写入私人库的唯一正式位置；一次表现不自动升级成长期写作规则。

## 案例、钩子与写作记忆

用户明确要求新增、更新或维护完整案例时读取 `references/content-case-library.md` 并使用：

```text
python <content-system-skill>/scripts/content_case_library.py
```

用户明确要求保存或维护独立钩子时读取 `references/hook-library.md` 并使用：

```text
python <content-system-skill>/scripts/hook_library.py
```

完整案例与独立钩子是两个真源，不能互相派生、复用同一条目或合并索引。写作入口只沿索引读取完整正文，本 Skill 负责维护，不替写作者决定怎样使用。

用户明确要求查询发布历史、内容查重、作者声音或维护写作记忆时读取 `references/personal-writing-memory.md` 并使用：

```text
python <content-system-skill>/scripts/writing_memory.py
```

发布历史只证明以前出现过什么；作者声音只使用用户明确认可且来源合格的作品。两类检索不能互相代替，发布效果也不自动改写用户声音。

## 与学习和写作的交接

材料需要先理解、研究或核查时，由 `$100x-learning` 产生准确的认识和来源，再把这些真实结果作为当前内容决定的材料。内容方向、分享候选或发布复盘完成后，用户要求成文时只把用户要求、原始材料、必要研究结果和明确内容决定交给现有写作入口，不叠加另一套写作简报、结构方案或评分标准。

## 完成

默认先给出当前可用的分享选择、策略判断、选题、重复判断、作者声音证据或发布复盘。保存动作完成前重新读取正式文件并运行对应索引验证；只在真实正文、索引和私人库路径一致后说明已经维护。达到当前内容决定后停止，不自动写稿、制作媒体或发布。
