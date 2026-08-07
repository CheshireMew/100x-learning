<p align="center">
  <img src="./assets/readme/hero.png" width="100%" alt="100x Learning 把材料、主题和真实问题转化为理解、判断、使用和分享的结果">
</p>

<!-- readme-header:start -->

<p align="center">
  <strong>中文</strong> · <a href="./README.en.md">English</a> · <a href="./README.ja.md">日本語</a> | <a href="./SKILL.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">反馈</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X：@0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram：CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="博客：blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="个人主页：blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/100x-learning/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/100x-learning?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/100x-learning/forks"><img src="https://img.shields.io/github/forks/CheshireMew/100x-learning?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/100x-learning/blob/main/LICENSING.md"><img src="https://img.shields.io/github/license/CheshireMew/100x-learning?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

# 100x Learning

把一份材料、一个陌生主题或一个真实问题交给你的 Agent，得到现在能理解、判断、使用或分享的结果；如果你要长期推进，它还能根据真实反馈维护下一轮学习、选题和内容改进。

`100x-learning` 是一个遵循 [Agent Skills 开放格式](https://agentskills.io/specification)的学习与内容 Skill。它可以读取字幕、文章、链接、主题、观点、项目、现有草稿和发布反馈，再根据你真正要得到的结果选择材料理解、主题研究、概念解释、实践、内容审查、写作、持续选题或知识沉淀。它不是独立应用，也不依赖某一个特定 Agent 宿主。

首屏图表达的是这个 Skill 当前稳定的输入与结果关系，不是性能或效果倍率证明。

## 你会得到什么

### 学习与研究

- **读懂材料**：`读懂这份访谈，讲清主线，并标出最值得回看的片段。` → 内容脉络、关键关系、重点及其真实位置。
- **选择学习方法**：`我想学会 X，目前卡在 Y，应该怎样学？` → 针对当前目标和卡点的学习路径与练习方式。
- **研究或核查主题**：`研究 X，并比较 A 与 B 哪个更适合我的目标。` → 与问题对应的来源、判断和仍然未知的部分。
- **解释或应用概念**：`用一个真实场景讲清 X，再用它分析 Y。` → 最低充分解释、机制、例子和可执行判断。

### 持续学习与内容

- **连续学习一个主题**：`围绕 X 连续学习。先完成当前最有用的一课，再根据我的反馈决定下一篇。` → 当前一课的可用结果，以及由真实反馈决定的下一步。
- **维护长期内容方向**：`根据我的目标和现有内容建立长期方向，并筛出这周值得做的选题。` → 内容方向、持续选题状态和对应的知识真源；不靠打分凑数量。
- **复盘已发布内容**：`结合最终正文、过去 7 天数据和评论复盘这篇内容。` → 分开的结果观察、候选解释、其它解释和下一次验证。

### 审查、写作与知识库

- **审查现有内容**：`只检查这篇稿子的事实、结构和 AI 味，不要改稿。` → 问题、影响和修改方向；没有授权时停在审查。
- **写成可发布内容**：`把这些材料写成一篇面向普通读者的中文 Thread。` → 可直接使用的短帖、Thread、项目介绍或文章。
- **设计发布内容**：`为这个项目设计发布期内容，先给方案。` → 按普通内容方案选择角度和参考；出现福利、时间或入口时再核对发布事实。
- **使用私人知识库**：`把确认后的结论保存到我的私人知识库。` → 先定位唯一库根，再更新同主题真源；只有明确要求时才写文件。

不同结果有不同停止位置。只要候选就不会自动继续写成帖子，只要审查就不会顺手改稿；新宣发请求明确要文字时直接交付成稿，只有明确要方案时才停在方案。保存、制作媒体和实际发布也都需要单独说明。

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

## 从一次任务继续到下一轮

一次性任务不需要先建立复杂系统：材料足够时，Skill 会直接完成解释、研究、判断或写作并停止。只有你明确要连续学习、维护长期内容方向、持续选题或保存结果时，它才会使用私人知识库保存跨任务状态。

持续任务遵循同一条反馈链：先锁定本轮真实输入和产物，再读取指标、评论、实际使用或你的直接反馈，最后决定下一课、下一题或下一次实验。单次发布表现只是一条待验证的线索，不会自动改写长期策略、个人声音或知识结论。

```text
使用 $100x-learning 维护这个系列的持续选题。
先读取已经确认的内容方向和现有选题，结合本周目标筛选下一批；
不要为了凑数量打分，也不要把一次临时要求写成长期策略。
```

## 它怎样处理一项任务

`SKILL.md` 是唯一总入口。它先根据用户最终要得到的结果选择路径，再按需读取 `references/` 中的对应方法。材料理解、主题研究、写作、持续选题和发布复盘使用不同流程：研究负责弄清事实；所有可发布文字首先服务传播，让读者尽快知道在讲什么、为什么值得继续看，并沿用户指定的重点读完、理解、记住或行动。写作前的联网只寻找用户材料没有提供的场景、机制、比较、反应和自然说法，不重新确认用户已经给出的数字、日期、条件或结论；草稿完成后才核对写作者新增或外部补充材料带来的主张。复盘则从真实成品和反馈中形成下一次可验证的改进。

写作任务还会分开管理完整案例、独立钩子和个人声音。任务合同只保留用户要求的成品和这篇文字要完成的传播结果，材料里的数字、规则和字段继续作为写作材料，不会变成另一套内容目标。普通新写、扩写和实质重组在动笔前必须从私人库完整读取多份案例与钩子；案例先匹配本次公开动作与推进关系，题材最后才用于缩小范围，钩子则要实际改变开头怎样接住后文。案例和钩子使用不同目录、脚本、类型和索引，但会共同进入成文上下文。对象和变化本身已经清楚时可以直接开场，短内容迅速把一件事说清，文章和 Newsletter 让各部分持续推进同一个重点。最终固定展示任务合同、实际使用的任务与材料、完整成品、创作参考和信息来源。推广、招募、预热和发布期内容仍走同一套普通写作流程；正文确实包含福利、时间、入口或披露时，才把普通读者需要的发布事实叠加进去。

它不会让所有任务绕行一条写作流水线：只要求读懂材料时停在解释，只要求研究时保留来源和未知项，只要求审查时不改稿；明确要求文字成品时直接完成成稿，只有明确要求内容方案时才停在方案。一次性选题不会自动变成长期项目，初始化知识库、保存文件、制作媒体和实际发布也分别需要明确请求。

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

默认库根记录在当前用户的 `~/.100x-learning/config.json`。接入后，私人库可以提供知识真源、完整内容案例、钩子、已确认的写作声音和发布历史。没有配置私人库时，材料理解和独立研究仍可使用当前输入与外部来源完成；普通新写、扩写和实质重组会在联网与外部材料发现前停止，并明确告诉用户先初始化或接入私人库，不会静默改成无参考写作。只有明确属于用户本人现稿的字词、格式或等义压缩可以直接按局部修改完成。

长期内容方向与个人声音使用不同真源；持续选题只保存当前系列的决策状态；发布复盘链接最终正文和真实反馈，不复制一份新的正文或指标数据库。只有重复证据、直接行为证据或用户确认支持的认识，才会进入长期真源。

### 保存边界

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
| 本身已经是完整成品，并且值得作为写作参考 | 完整短内容或文章案例目录 | 从第一句到最后一句保留完整正文和必要定位字段，不附加来源，并进入内容案例索引 |
| 用户明确指定保存的一段原始开头 | `20-Sources/Hook Library/<写作格式>` | 保存连续原文、紧接内容和最少定位字段，不附加来源，并进入独立钩子索引 |
| 用户确认的终稿或已发布作品 | `40-Outputs/Writing` | 保存最终正文，并按真实来源决定是否进入发布历史或作者声音检索 |

一次材料可以产生来源记录、知识增量或完整案例；钩子只由用户明确的钩子保存动作产生。写入完成后，Skill 会重新读取实际真源并重建案例或钩子的独立索引，让下一次检索和写作真正读到结果。

正式文章需要成为案例时会复制一份到 `20-Sources/Articles/Content Cases`。正式文章保留发布入口，案例副本不带来源；两种角色不会共用同一文件。

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

测试覆盖的是完整生产与消费链：新库会从空目录初始化，再由独立进程通过本机指针重新定位和验证；真实 UTF-8 材料分别经过 `content_case_library.py add-case` 和 `hook_library.py add-hook` 写入两个真源，各自索引随后由正式读取入口消费；明确带有写作元数据的案例还会继续进入写作记忆检索。测试不会由消费端手写一份假索引来冒充生产者结果。

## 能力边界

这个 Skill 负责理解材料、研究主题、解释概念、设计实践、审查内容，以及写作短帖、Thread、GitHub 项目介绍、文章和需要承接发布事实的内容。图片、GIF、视频、音频与播客制作，普通翻译，广告投放，销售页、邮件营销序列、品牌全案、完整营销策略和实际发布不属于它的交付范围，需要另行选择对应能力。

文件写入、媒体制作、上传和发布互不代替。没有明确授权时，结果只保留在当前回复或本地工作区。

## 许可证

仓库原创的 Skill 指令、源码、测试、脚本和可复用模板采用 [Mozilla Public License 2.0](./LICENSE)。`archive/`、`output/`、导入的案例、来源文章、社交帖子、截图及其它第三方或参考内容不在这项授权范围内；完整边界见 [LICENSING.md](./LICENSING.md)。

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>
