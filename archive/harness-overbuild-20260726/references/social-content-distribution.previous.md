# 平台内容组合设计

<!-- 旧 distribution_plan 与 Harness 流程，已退出活动 Skill。 -->

用于把已经确认的内容真源转化为一条或多条平台原生短内容。该流程负责成文前的编辑决策；实际文字及后续修订由当前 Agent 直接完成。

## 一、进入条件与交付边界

用户明确要求以下任一结果时进入本流程：

- 面向 LinkedIn、X 或其它指定平台的独立帖子、Thread 或短文案。
- 从同一份材料生成多条角度不同的分发内容。
- 带有平台限制、互动目标、资源链接或首条评论／回复 CTA 的发布级文字包。

通用的单条独立短内容可以继续使用普通成文路径。用户只要求筛选分享候选时停在内容真源交接包；文章和 Newsletter 进入文章流程；卡片、视频、音频及其它媒体成品交给 `visual-multimedia`。

本流程的输入是已经确认的 `subject`、`core_message` 和 `content_truth`。分发计划选择怎样表达这些内容，不增加新的事实、经历、数据、引语、来源或结果。

## 二、建立唯一分发计划

成文前建立 `distribution_plan`。该对象是平台选择、内容拆分、帖子差异、互动方式、CTA、平台规则和热点使用的唯一活动计划：

```json
{
  "primary_reader": {
    "role": "读者的具体角色",
    "context": "读者所处的工作、生活或认知场景",
    "job": "读者想完成的事情",
    "pain": "当前阻力、误解或代价",
    "desired_outcome": "读者希望得到的变化",
    "awareness": "读者目前知道什么、尚未理解什么",
    "objection": "有来源依据的主要异议；未知时使用空字符串"
  },
  "reader_action": "读完后能够判断、尝试、保存、讨论或继续查看什么",
  "content_atoms": [
    {
      "id": "atom-1",
      "type": "claim",
      "content": "能够独立使用的内容单元",
      "source_boundary": "来源位置、事实状态、条件和适用范围"
    }
  ],
  "portfolio": [
    {
      "id": "post-1",
      "platform": "目标平台或通用社媒",
      "format": "单帖、Thread 或其它明确格式",
      "job": "这条内容在整个组合中承担的任务",
      "angle": "这条内容的唯一表达角度",
      "atom_ids": ["atom-1"],
      "hook_strategy": "与内容原子和证据匹配的开头策略",
      "value_delivery": "正文怎样兑现开头并让读者得到东西",
      "engagement": "有实际内容的回应、保存或讨论方式",
      "cta": {
        "mode": "none",
        "promise": "",
        "destination_status": "not_needed",
        "destination": ""
      }
    }
  ],
  "platform_checks": [
    {
      "platform": "与 portfolio 中一致的平台",
      "status": "verified",
      "checked_at": "YYYY-MM-DD",
      "sources": ["当前官方规则的直接链接"],
      "constraints": ["会改变正文或发布方式的当前规则"]
    }
  ],
  "trend": {
    "status": "not_requested",
    "bridge": "",
    "sources": []
  }
}
```

这份计划只服务内部选择和校验。`content_atoms`、`portfolio`、`hook_strategy`、`value_delivery`、`engagement` 和 `bridge` 等字段名不进入发布正文；当前 Agent 读取字段中的含义，再按 `content-writing.md` 写成目标读者能够直接理解的内容。

稳定取值如下：

- `content_atoms[].type`：`claim`、`data`、`insight`、`framework`、`story`、`proof`、`quote`、`objection`、`resource`。
- `cta.mode`：`none`、`body`、`first_comment_or_reply`。
- `cta.destination_status`：`not_needed`、`provided`、`source_url`、`missing`。
- `platform_checks[].status`：`verified`、`not_required`、`unavailable`。
- `trend.status`：`not_requested`、`not_used`、`used`、`unavailable`。

## 三、形成内容原子与具体读者

从 `content_truth` 中提取能够分别支撑独立内容的原子：

- `claim` 保存有边界的主张。
- `data` 保留数字、单位、样本、时间和条件。
- `insight` 保存由材料支持的含义或判断。
- `framework` 保存步骤、清单、模型或决策规则。
- `story` 保存真实场景、阻力、转折和结果。
- `proof` 保存案例、截图、实验、输出或可观察结果。
- `quote` 只保存已经核对的原文，并在 `source_boundary` 中记录位置和状态。
- `objection` 保存材料中真实存在的异议、代价或限制。
- `resource` 保存文章、报告、工具、模板、链接或其它后续入口。

每个原子都有唯一 `id`，并且能够回到 `content_truth`。条件和来源状态跟随原子进入后续帖子，避免数据、引语和结果脱离原始边界。

读者信息优先使用用户已经指定的受众。用户只给出宽泛受众时，从材料中的问题、语言、例子和使用场景确定最具体且有证据支持的读者状态；多个选择会改变大部分内容时，只确认这一项。`primary_reader` 描述同一组内容服务的主要读者，用户明确要求多个受众时再为不同分组建立各自计划。

## 四、设计内容组合

`portfolio` 的数量和平台服从用户请求。用户只要求通用社媒短内容时使用“通用社媒”，不擅自指定平台。每个条目先确定读者获得的价值，再确定表达形式：

1. `job` 说明它负责建立判断、提供方法、展示证据、讲述经历、回应异议或连接资源中的哪一项。
2. `angle` 只承载一个能够独立成立的观点。
3. `atom_ids` 指向真正支撑这条内容的原子。
4. `hook_strategy` 根据原子选择信念修正、隐藏原因、数据发现、前后变化、真实错误、取舍、方法、资源、故事或及时变化等结构。
5. `value_delivery` 说明正文在开头后的前一至三段怎样兑现承诺。
6. `engagement` 给读者一个具体的判断、经验、取舍、补充或保存理由；正文不需要互动时写明自然收束方式。

多条内容保持共同读者和内容真源，同时让任务、角度、主要原子、开头策略和互动方式产生可观察差异。必要事实可以复用，但每次复用都要带来不同含义。每条内容脱离其它条目后仍能让读者理解并得到完整价值。

## 五、平台规则、热点与 CTA

用户要求指定平台的可发布正文，或者字符、链接、媒体、Thread、首条评论和回复行为会改变交付时，读取当前官方规则，并把核查日期、直接来源和会影响成品的限制写入 `platform_checks`。通用内容或不依赖具体规则的草稿使用 `not_required`；官方来源暂时无法核实时使用 `unavailable`，成品只承诺已经确认的部分。

热点适配由用户明确要求、或当前变化本身构成内容主线时触发。先验证近期来源，再说明它与核心主张和具体读者之间的直接联系：

- 找到并使用真实联系时，`trend.status` 使用 `used`，同时填写 `bridge` 和直接来源。
- 用户要求热点但没有合适联系时使用 `not_used`。
- 无法完成当前核实时使用 `unavailable`。
- 其余请求使用 `not_requested`。

CTA 由交付目标和真实入口决定：

- 无需后续动作时使用 `none`、`not_needed`，其它 CTA 字段保持空字符串。
- 正文或首条评论／回复需要交付资源时，`promise` 写清读者会得到什么。
- 用户提供链接时使用 `provided`；内容真源中的文章链接承担入口时使用 `source_url`。
- CTA 已经确定但缺少入口时使用 `missing`，`destination` 保持空字符串，最终交付明确标出待补链接。

正文中的承诺、CTA 的资源价值和实际链接指向保持一致。

## 六、校验并直接成文

先运行确定性门禁：

```powershell
python -m harness validate-distribution distribution-plan.json
```

通过后建立 `content-writing.md` 规定的唯一写作输入，让内容真源、当前作者声音、对应模板、同类型完整案例和已经校验的分发计划同时进入当前 Agent：

- `subject`、`core_message` 和 `content_truth` 保持事实与信息真源职责。
- `audience` 概括 `primary_reader`，便于普通写作验收。
- `deliverable` 写明平台、条数、格式、使用场景和读者结果。
- `shareable_point` 与 `writing_job.core_information` 保存用户的观点取向、信息取舍和主张边界；`author_voice` 保存当前用户原话、有效正文、确认稿、已发布内容和声音档案支持的表达方式。
- `writing_job.requirements` 保存本次组合仍然有效的平台、注意力、阅读感受、信息密度、张力、固定文字和其它要求。
- `writing_templates` 读取基础成文模板与本文件，`writing_examples` 读取当前内容类型的完整 `short` 案例；用户明确要求病毒式传播时再加入 `hook`。
- `distribution_plan` 原样保留已经通过校验的结构化计划。

当前 Agent 根据同一份写作输入完成全部正文后，按以下可观察结果验收：

1. 输出包含 `portfolio` 约定的全部条目和对应 CTA。
2. 每条内容的主张、数据、经历、引语和资源都能回到所引用的内容原子及 `content_truth`。
3. 开头在前一至三段得到正文兑现。
4. 多条内容在任务、角度、主要原子、开头策略和互动方式上确实不同。
5. 每条内容能够独立阅读，平台格式符合已经记录的当前约束。
6. CTA 的承诺、入口状态和目的地一致；缺失入口已经显式标明。
7. 使用热点时，正文表达与 `bridge` 和来源一致。
8. 发布正文没有复述内部字段名、内容原子类型或分发计划标签；这些结构只通过选材、顺序、节奏和行动设计影响成品。

发现偏差时保留仍然有效的 `distribution_plan`，由当前 Agent 根据当前正文和具体问题直接修改。用户只调整措辞时保持计划；用户改变受众、平台、条数、核心信息、资源入口或内容任务时先更新计划并重新校验。

## 七、输出、视觉交接与停止

最终交付先给可直接使用的正文及其首条评论／回复，再提供确实影响发布的规则核查、链接缺口或热点来源。内部内容原子、候选开头和分发计划只在用户要求时展示。

用户选定某条内容并要求媒体方案或成品时，向 `visual-multimedia` 交接：

- 选中的 `portfolio[].id` 和完整正文。
- 该条内容的核心观点、引用原子和关键证据。
- `primary_reader` 与读者应当看懂或记住的认知锚点。
- 内容真源中的来源、版权状态和现有素材。
- 当前 `author_voice` 的真实来源、声音信号和明确保留的表达选择。
- 当前任务属于系列派生时，交接来源标识、来源版本和内容单元标识。

媒体流程负责选择视觉任务、载体、结构、风格和生成方式。新事实、数据或结果先回到 `content_truth` 和 `distribution_plan`，再进入媒体成品。

正文、CTA、必要发布说明和用户要求的保存位置均已交付，并通过内容真源、组合差异和平台约束验收后停止。媒体制作、排期、上传和发布由各自请求触发。
