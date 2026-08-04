<p align="center">
  <img src="./assets/readme/hero.png" width="100%" alt="100x Learning 把材料、主题和真实问题转化为理解、判断、使用和分享的结果">
</p>

# 100x Learning

把一份材料、一个陌生主题或一个真实问题交给你的 Agent，得到现在能理解、判断、使用或分享的结果。

`100x-learning` 是一个遵循 [Agent Skills 开放格式](https://agentskills.io/specification)的学习与内容 Skill。它可以读取字幕、文章、链接、主题、观点、项目和现有草稿，再根据你真正要得到的结果选择材料理解、主题研究、概念解释、实践、内容审查、写作或知识沉淀。它不是独立应用，也不依赖某一个特定 Agent 宿主。

首屏图表达的是这个 Skill 当前稳定的输入与结果关系，不是性能或效果倍率证明。

## 你会得到什么

| 你想得到什么 | 可以怎样提问 | Skill 会交付什么 |
| --- | --- | --- |
| 读懂材料 | `读懂这份访谈，讲清主线，并标出最值得回看的片段。` | 内容脉络、关键关系、重点及其真实位置 |
| 选择学习方法 | `我想学会 X，目前卡在 Y，应该怎样学？` | 针对当前目标和卡点的学习路径与练习方式 |
| 研究或核查主题 | `研究 X，并比较 A 与 B 哪个更适合我的目标。` | 与问题对应的来源、判断和仍然未知的部分 |
| 解释或应用概念 | `用一个真实场景讲清 X，再用它分析 Y。` | 最低充分解释、机制、例子和可执行判断 |
| 审查现有内容 | `只检查这篇稿子的事实、结构和 AI 味，不要改稿。` | 问题、影响和修改方向；没有授权时停在审查 |
| 写成可发布内容 | `把这些材料写成一篇面向普通读者的中文 Thread。` | 可直接使用的短帖、Thread、项目介绍或文章 |
| 设计发布内容 | `为这个项目设计发布期内容，先给方案。` | 按普通内容方案选择角度和参考；出现福利、时间或入口时再核对发布事实 |
| 使用私人知识库 | `把确认后的结论保存到我的私人知识库。` | 先定位唯一库根，再更新同主题真源；只有明确要求时才写文件 |

不同结果有不同停止位置。只要候选就不会自动继续写成帖子，只要审查就不会顺手改稿，新宣发请求默认先交付方案，保存、制作媒体和实际发布也都需要单独说明。

## 快速开始

把完整仓库放进兼容工具所读取的 Skills 目录。支持项目级 `.agents/skills/` 的工具可以直接运行：

```bash
git clone https://github.com/CheshireMew/100x-learning.git .agents/skills/100x-learning
```

如果你的工具使用用户级目录或其它位置，把最后的目标路径替换为它自己的 Skills 目录。Agent Skills 是开放格式；同一个 Skill 可以被不同的兼容 Agent 加载，具体发现目录和显式调用语法由宿主决定。[官方快速入门](https://agentskills.io/skill-creation/quickstart)给出了项目级目录示例。

安装后可以直接描述目标：

```text
读懂这份材料。先忠实讲清内容、主线和关键关系，
再告诉我哪些部分最值得继续深挖。
```

支持显式点名 Skill 的工具也可以使用 `$100x-learning`。第一次成功时，你拿到的应该是材料本身的清楚解释，而不是一份空泛的学习建议或内部流程说明。

## 它怎样处理一项任务

`SKILL.md` 是唯一总入口。它先根据用户最终要得到的结果选择路径，再按需读取 `references/` 中的一项方法。材料理解、主题研究和写作使用不同流程：研究负责弄清事实，写作负责从已经筛选过的材料中形成自然成品，成稿后只核查真正写进正文、并会改变读者理解或行动的说法。

写作任务还会分开管理完整案例、独立钩子和个人声音。案例与钩子使用不同目录、脚本、类型和索引，但在成文时可以同时作为参考。推广、招募、预热和发布期内容仍走同一套普通写作流程；正文确实包含福利、时间、入口或披露时，才把这些发布事实叠加进去并在成稿后按实际承诺核查。

它不会让所有任务绕行一条写作流水线：只要求读懂材料时停在解释，只要求研究时保留来源和未知项，只要求审查时不改稿；只有明确要求文字成品时才进入写作。新宣发请求默认先给可确认方案，初始化知识库、保存文件、制作媒体和实际发布分别需要明确请求。

## 私人知识库与公开仓库

私人知识库位于 Skill 目录之外，不随公开仓库分发。用户明确要求后，可以初始化一个新库，或接入符合当前目录合同的已有 Markdown 知识库：

```text
使用 $100x-learning 初始化私人知识库，位置是 D:\Knowledge\100x-learning。
使用 $100x-learning 接入现有私人知识库，位置是 E:\Knowledge\Existing Library。
```

不支持 `$skill-name` 显式调用语法的 Agent，可以直接使用同样的自然语言目标。底层对应命令是：

```powershell
python scripts/private_library.py init --root "D:\Knowledge\100x-learning"
python scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
python scripts/private_library.py show
python scripts/private_library.py validate
```

默认库根记录在当前用户的 `~/.100x-learning/config.json`。接入后，私人库可以提供知识真源、完整内容案例、钩子、已确认的写作声音和发布历史；没有接入时，材料理解、研究和写作仍然可以使用当前输入正常完成。只有结果必须持久化但还没有可用库根时，Skill 才会询问保存位置。

新建库必须位于 Skill 源码目录之外；目标目录已经有内容时，初始化器不会把它当成空库覆盖，而是要求明确使用 `adopt`。接管已有库只增加 100x Learning 的库标识并更新本机根目录指针，不移动、复制或改写已有知识内容；目录合同不完整时会在写入标识前停止。配置文件只保存库版本和根目录，不保存私人正文。

初始化完成后，可以明确要求把用户材料沉淀进去：

```text
阅读这份材料并沉淀到我的私人知识库。保留值得长期复用的知识；如果它本身是完整成品，再判断是否进入内容案例。除非我明确指定一段连续的原始开头保存为钩子，否则不要建立钩子。
```

写入只在用户明确要求时发生。原始材料、稳定知识、完整案例和独立钩子服务不同用途。知识文档链接来源；案例和钩子分别由用户动作触发并写入独立真源，不能从案例自动派生钩子，也不能在钩子中保存案例路径。

### 材料会沉淀到哪里

| 材料实际角色 | 私人库位置 | 处理结果 |
| --- | --- | --- |
| 网页、课程、字幕、访谈、原帖等原始材料 | `20-Sources` | 保留出处、来源角色和必要上下文；需要长期保留且允许保存时才写入全文 |
| 已经消化的概念、机制、结论和适用边界 | `10-Knowledge` | 先搜索同主题和别名，更新唯一主题真源；只有独立问题才新建文档 |
| 本身已经是完整成品，并且值得作为写作参考 | 完整短内容或文章案例目录 | 从第一句到最后一句保留完整正文和可核对来源，并进入内容案例索引 |
| 用户明确指定保存的一段原始开头 | `20-Sources/Hook Library/<写作格式>` | 保存连续原文、紧接内容、来源和最少定位字段，并进入独立钩子索引 |
| 用户确认的终稿或已发布作品 | `40-Outputs/Writing` | 保存最终正文，并按真实来源决定是否进入发布历史或作者声音检索 |

一次材料可以产生来源记录、知识增量或完整案例；钩子只由用户明确的钩子保存动作产生。写入完成后，Skill 会重新读取实际真源并重建案例或钩子的独立索引，让下一次检索和写作真正读到结果。

克隆公开仓库不会带走私人资料，也不会自动获得某个人的经历、立场或写作声音。仓库交付的是工作流、方法、初始化模板、维护脚本和行为测试。

## 项目结构

```text
100x-learning/
├── SKILL.md                   # 通用总路由、行为边界与交付规则
├── agents/openai.yaml         # OpenAI 宿主中的展示与默认提示信息
├── references/                # 学习、研究、写作和知识库方法
├── scripts/                   # 字幕、私人库、案例和写作记忆工具
├── assets/private-library/    # 初始化私人库所需的公开模板
├── assets/readme/             # GitHub 主页视觉素材
├── tests/                     # 路由、能力守恒和资源边界测试
└── archive/                   # 已退休资料，不参与当前运行
```

活动能力由 `SKILL.md`、当前 `references/`、`scripts/`、公开资产、元数据和测试共同定义。`agents/openai.yaml` 是宿主适配信息，不改变项目作为通用 Agent Skill 的身份；`archive/` 中的旧路由和旧脚本不会被恢复成当前能力。

## 维护与验证

维护脚本使用 Python 标准库。先运行完整行为测试：

```bash
python -m unittest discover -s tests -v
```

整理 SRT、VTT 或带时间戳的文本时，可以保留真实时间边界并输出 Markdown：

```bash
python scripts/normalize_subtitles.py path/to/input.srt > normalized.md
```

已经配置私人知识库时，可维护内容案例和写作记忆：

```bash
python scripts/content_case_library.py build-index
python scripts/content_case_library.py validate
python scripts/writing_memory.py build-index
python scripts/writing_memory.py validate
```

测试覆盖的是完整生产与消费链：新库会从空目录初始化，再由独立进程通过本机指针重新定位和验证；真实 UTF-8 材料分别经过 `content_case_library.py add-case` 和 `hook_library.py add-hook` 写入两个真源，各自索引随后由正式读取入口消费；符合写作来源条件的案例还会继续进入写作记忆检索。测试不会由消费端手写一份假索引来冒充生产者结果。

## 能力边界

这个 Skill 负责理解材料、研究主题、解释概念、设计实践、审查内容，以及写作短帖、Thread、GitHub 项目介绍、文章和需要承接发布事实的内容。图片、GIF、视频、音频与播客制作，普通翻译，广告投放，销售页、邮件营销序列、品牌全案、完整营销策略和实际发布不属于它的交付范围，需要另行选择对应能力。

文件写入、媒体制作、上传和发布互不代替。没有明确授权时，结果只保留在当前回复或本地工作区。

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>
