# DeepSeek 内容成文（已归档）

用于把 100x Learning 已经整理、核实并确定边界的内容写成独立短帖、GitHub 项目短介绍、Thread、短文案、文章或 Newsletter。最终文字生产者固定为 DeepSeek V4 Pro；研究、判断、结构设计和交付验收仍由主流程负责。

## 一、何时调用

用户已经授权起草或改写以下文字时，必须读取本文件并调用 `scripts/deepseek_content_writer.py`：

- 能够脱离媒体独立成立的单条帖子、Thread、短文案和引导帖。
- 已经按 `references/github-project-short-content.md` 建立事实集与呈现合同的 GitHub 项目短介绍。
- 文章和 Newsletter。
- 对上述成品进行结构、声音、节奏、语言或内容修订。

分享候选识别、媒体制作、研究材料、事实核查、声音分析、内容审计、知识讲解、学习诊断和写作大纲继续按各自主流程完成。卡片内文字、视频口播、字幕、播客串词和与某个媒体成品共同设计的配套帖子由 `visual-multimedia` 负责；用户在那里明确点名 DeepSeek 时切换写作入口。逐字引用、来源名称、数据标签和用户已经确认保持原样的文本直接传递。

## 二、调用前先形成内容包

调用脚本前，把当前任务整理成一个 JSON 对象：

```json
{
  "action": "draft",
  "content_mode": "general",
  "subject": "本次成品介绍、讨论或表达的唯一对象",
  "core_message": ["按重要性排列、读者最终必须记住的核心信息"],
  "content_truth": "能够支撑核心信息的事实、经历、例子、引语、来源及其状态",
  "audience": "目标读者及其必要背景",
  "deliverable": "交付类型、使用场景和读者看到成品后应当获得的结果",
  "editorial_position": {
    "source": "观点取向的已确认来源",
    "position": "作者在当前主题上的判断和评价方向",
    "selection_rules": ["哪些信息优先进入正文，以及怎样取舍"],
    "claim_boundaries": ["作者说到哪里，哪些判断仍然未知或不成立"]
  },
  "voice_contract": {
    "narrative_driver": "文章或内容怎样推进",
    "point_of_view": "主要视角",
    "opening": "开头方式",
    "layout": "段落、标题、列表和版式习惯",
    "media_role": "图片、截图、数据或其它媒体怎样承担信息",
    "humor_mechanism": "幽默或反差怎样产生",
    "ending": "结尾方式",
    "avoid": ["经过确认的表达禁区"],
    "stable_traits": ["长期确认的声音特征"],
    "sample_specific_traits": ["只来自当前样稿的倾向；可以为空"]
  },
  "creative_direction": "本次成品的注意力任务、阅读感受、信息密度、传播张力和读者反应",
  "hard_constraints": ["用户或目标平台明确提出的硬要求；没有时使用空数组"]
}
```

`editorial_position` 和 `voice_contract` 是可选字段。用户明确以本人、固定角色或连续系列表达，或者当前项目已经有经过确认的长期定位时才加入；普通研究解释、无固定作者身份的写作和证据不足的个人化请求省略它们。两个字段一旦加入，draft、自动修订和用户后续 revise 都原样保留，直到用户更新对应来源。

`content_mode` 是写作合同的判别字段：

- `general` 用于通用单条短内容、文章和 Newsletter，内容包不包含 `distribution_plan`。
- `github_project_short` 用于 GitHub 项目短介绍，内容包不包含 `distribution_plan`；项目事实集、系列关系和呈现合同先由 `references/github-project-short-content.md` 确定。
- `social_distribution` 用于指定平台、多条差异化短内容或带 CTA 的发布级文字包，内容包必须原样包含已经按 `references/social-content-distribution.md` 建立并通过门禁的 `distribution_plan`。

平台内容的读者状态、内容原子、帖子任务、平台规则、热点和 CTA 只由 `distribution_plan` 决定；`editorial_position` 决定作者怎样评价和取舍这些内容原子，`voice_contract` 决定稳定表达方式，`creative_direction` 只承担本次组合的注意力任务、阅读感受、信息密度和传播张力。需要改变受众、平台、条数、主要内容原子、资源入口或帖子任务时先更新计划，再重新校验和调用写作脚本。

`subject` 在读取材料前确定。优先使用用户明确点名的对象，其次使用用户提供的文件或仓库、当前对话持续讨论的主题和当前工作目录。多个合理对象会产生不同正文时，先询问对象；已经唯一明确时直接继续。

`core_message` 是正文的信息主线，顺序代表优先级。用户明确给出的主张直接进入这里；来源材料用于补充证明和必要语境，辅助信息保持在用户指定重点之后。`content_truth` 是事实唯一真源，保留事实、个人判断、推断、修辞、引语和待确认信息之间的区别；成品中的每项可核验信息都能追溯到这里。

`editorial_position` 的来源必须能够回到用户当前明确指令、用户确认稿、已发布内容或维护中的定位档案。它只决定作者确认过的判断、评价方向、信息取舍和主张边界。`voice_contract` 使用 `validate-writing` 已经采用的完整声音结构，区分长期确认的稳定特征与当前样稿倾向；它只决定视角、推进、段落、素材作用、幽默、结尾和表达习惯。`creative_direction` 用积极、具体的结果引导本次创作，包括希望读者看见什么、感到什么、为什么愿意停留或转发，以及当前成品需要的密度和张力。模型在这三类输入各自的职责范围内选择传播技巧、篇幅和结构。`hard_constraints` 可以为空，只收录用户或目标平台明确提出的硬要求。

修改现有成品时使用同一个结构，并改为：

```json
{
  "action": "revise",
  "content_mode": "general",
  "subject": "本轮唯一写作对象",
  "core_message": ["本轮仍然有效、按重要性排列的核心信息"],
  "content_truth": "本轮仍然有效的内容真源",
  "audience": "目标读者",
  "deliverable": "修订后需要达到的交付结果",
  "editorial_position": {
    "source": "沿用或更新后的已确认来源",
    "position": "本轮仍然有效的作者判断和评价方向",
    "selection_rules": ["本轮仍然有效的信息取舍规则"],
    "claim_boundaries": ["本轮仍然有效的主张边界"]
  },
  "voice_contract": {
    "narrative_driver": "本轮仍然有效的推进方式",
    "point_of_view": "主要视角",
    "opening": "开头方式",
    "layout": "版式习惯",
    "media_role": "媒体职责",
    "humor_mechanism": "幽默机制",
    "ending": "结尾方式",
    "avoid": ["表达禁区"],
    "stable_traits": ["长期确认特征"],
    "sample_specific_traits": ["当前样稿倾向；可以为空"]
  },
  "creative_direction": "本轮有效的注意力任务、阅读感受、信息密度和传播张力",
  "hard_constraints": ["本轮明确的硬要求；没有时使用空数组"],
  "current_text": "当前有效正文",
  "revision_request": "本轮明确要求修正的问题和范围"
}
```

`github_project_short` 的 draft 和 revise 内容包沿用上述字段，把事实状态与来源保留在 `content_truth`，把项目关系放进 `core_message`，把开头作用、篇幅、正文形态、emoji、链接和结尾放进 `creative_direction` 与 `hard_constraints`。个人或系列化项目介绍需要稳定作者判断或表达方式时，再加入 `editorial_position` 与 `voice_contract`。`social_distribution` 的 draft 和 revise 内容包在上述字段之外都包含同一个 `distribution_plan` 字段。当前有效正文由用户最新确认或当前指定的版本决定。用户纠正对象或核心信息时先重建 `subject` 与 `core_message`；用户改变观点取向时只更新 `editorial_position`，改变表达方式时只更新 `voice_contract`，改变本次传播任务时只更新 `creative_direction`；用户改变项目呈现合同时先更新 GitHub 专项事实包，改变分发决策时同步更新并重新校验 `distribution_plan`。活动内容包只收录本轮有效内容。

## 三、调用唯一写作入口

默认配置文件位于仓库外的 `D:\Tools\100x-learning\deepseek.env`，只包含本地密钥：

```text
DEEPSEEK_API_KEY=<local-only>
```

也可以通过进程环境变量 `DEEPSEEK_API_KEY` 或 `DEEPSEEK_ENV_FILE` 指向本地配置。密钥只存在于进程环境或仓库外的本地配置。

先在需要时检查账户与模型是否可用：

```powershell
python scripts/deepseek_content_writer.py check
```

内容包可以通过文件或标准输入传入：

```powershell
python scripts/deepseek_content_writer.py write --input packet.json --output draft.md
```

脚本固定调用官方 `deepseek-v4-pro`，思考配置采用该模型的服务默认值。标准输出提供最终正文，标准错误提供调用元数据。

## 四、验收和修订

收到正文后，沿当前真实链路核对：

1. 正文对象与 `subject` 一致。
2. `core_message` 按既定优先级成为正文主线，辅助事实服务于用户指定的重点。
3. 每项事实、经历、数字、引语和来源都能回到 `content_truth`。
4. 文字类型、使用场景和读者结果符合 `deliverable`；存在 `editorial_position` 时内容取舍与主张边界一致，存在 `voice_contract` 时表达方式一致，本次阅读效果体现 `creative_direction`，并遵守 `hard_constraints`。
5. 正文保留本轮明确有效的内容。
6. `github_project_short` 输出体现已经确认的项目角色、用户结果、事实强度、系列关系、活动呈现合同和项目入口，并通过 `references/github-project-short-content.md` 的验收。
7. `social_distribution` 输出完整实现 `distribution_plan.portfolio`，内容原子、帖子差异、平台核查、热点和 CTA 通过 `references/social-content-distribution.md` 的验收。
8. 输出文件或聊天内容直接使用脚本返回的正文。

脚本在返回正文前检查活动 Skill 明确禁止的预制二元对照句式；发现后自动建立一次保留当前内容包和 `distribution_plan` 的 `revise` 请求。修订结果仍未通过时停止交付并报告门禁失败。

其它问题由 Agent 把当前正文、具体问题和仍有效的内容真源组成 `revise` 内容包，再调用同一脚本。确定性格式处理负责用户要求的文件头、换行、编码或路径信息；措辞、结构、语气或内容修订由 DeepSeek 完成。

## 五、失败与停止

API 凭据无效、余额不足、模型不可用、请求中断或输出被截断时，立即说明具体阻断。写作生产者保持 DeepSeek V4 Pro；用户明确指定新的生产者时再迁移。

正文通过内容真源、文字类型和声音核对，并已经交付到用户要求的位置后停止。持久化资产只包含用户要求的正文与必要交付文件；思考内容、完整请求包和调用日志保持临时状态。
