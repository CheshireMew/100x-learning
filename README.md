<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>把学习、私人知识和内容改进分别交给清楚、可组合的入口。</strong>
</p>

<p align="center">
  <strong>中文</strong> · <a href="./README.en.md">English</a> · <a href="./README.ja.md">日本語</a> | <a href="./skills/100x-learning/SKILL.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">反馈</a>
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

`100x-learning` 是一个遵循 [Agent Skills 开放格式](https://agentskills.io/specification)的多 Skill 仓库。三个入口共享同一套长期资源合同，但分别完成学习、私人知识和内容系统结果，避免每次请求加载无关规则。

<p align="center">
  <img src="./assets/readme/hero.png" width="100%" alt="材料、主题和真实问题经过 100x Learning 形成理解、判断、使用和分享的机制图">
</p>

## 先告诉它你要什么

你不需要先理解内部流程，直接描述结果即可：

- **读懂材料**：`讲清这份访谈的主线、关键关系，并标出值得回看的片段。`
- **研究与判断**：`研究 X，比较 A 和 B 哪个更适合我的目标，并保留未知项。`
- **解释与实践**：`用真实场景讲清 X，再用它分析我遇到的 Y。`
- **连续学习**：`围绕 X 连续学习，先完成当前最有用的一课，再根据我的反馈决定下一步。`
- **沉淀知识**：`使用 $private-knowledge，把确认后的结论保存到私人知识库，并更新同主题真源。`
- **改进内容**：`使用 $content-system，复盘这篇已发布内容，并决定下一篇验证什么。`

每个 Skill 都会停在自己负责的结果：学习不会自动保存，分享候选不会自动写成帖子，一次复盘不会自动改写长期策略。可发布文字继续由 `prep-this`、`write-this` 和 `clean-copy` 负责。

## 快速开始

使用兼容 Agent Skills 的安装器安装整个仓库：

```bash
npx skills add CheshireMew/100x-learning
```

安装器会发现 `100x-learning`、`private-knowledge` 和 `content-system` 三个入口。也可以把仓库克隆到本地，再让宿主从 `skills/` 下安装所需入口。

安装后可以直接描述目标：

```text
读懂这份材料。先忠实讲清内容、主线和关键关系，
再告诉我哪些部分最值得继续深挖。
```

支持显式点名 Skill 的工具使用 `$100x-learning`、`$private-knowledge` 或 `$content-system`。第一次成功时，你拿到的应该是对应的真实结果，而不是内部路由说明。

## 它怎样保持结果对题

| 你的请求 | Skill 的处理 | 交付与停止位置 |
| --- | --- | --- |
| 读懂材料 | 忠实恢复内容、主线、关系和真实位置 | 清楚解释与重点，不扩成研究项目 |
| 研究或核查 | 比较来源，区分事实、判断和未知项 | 带来源的结论与仍待确认的问题 |
| 保存或检查知识 | 通过唯一私人库配置定位、写入和核对 | 可继续读取的正式知识与真实状态 |
| 选择分享内容 | 先理解完整材料，再按受众和用途取舍 | 分享候选与理由，不自动成文 |
| 复盘已发布内容 | 分开真实结果、解释和其它可能性 | 下一次可验证的内容决定 |

一次性任务不需要建立长期系统。只有你明确要求维护内容方向、保存结果、查询历史或读取个人声音时，对应 Skill 才会使用持久资料。

## 可选：私人知识库与持续工作

私人知识库位于 Skill 目录之外，不随公开仓库分发。你可以让 Agent 初始化新库，或接入现有 Markdown 知识库：

```text
使用 $private-knowledge 初始化私人知识库，位置是 D:\Knowledge\100x-learning。
使用 $private-knowledge 接入现有私人知识库，位置是 E:\Knowledge\Existing Library。
```

库根记录在当前用户的 `~/.100x-learning/config.json`，配置只保存版本和路径，不保存私人正文。`init` 不会覆盖非空目录；`adopt` 只增加项目标识并更新本机路径，不移动或改写现有知识。

接入后，`private-knowledge` 维护来源、同主题知识真源、项目和成果；`content-system` 使用同一个库维护完整案例、独立钩子、确认后的作品、内容方向和持续选题状态。两者不会建立第二套数据根。

<details>
<summary>直接运行知识库维护脚本</summary>

```powershell
python skills/private-knowledge/scripts/private_library.py init --root "D:\Knowledge\100x-learning"
python skills/private-knowledge/scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
python skills/private-knowledge/scripts/private_library.py show
python skills/private-knowledge/scripts/private_library.py validate
```

</details>

没有配置私人库时，材料理解、研究、分享筛选和当前回复中的内容判断仍然可以直接完成。克隆公开仓库也不会带走任何私人资料。

## 能力边界

本仓库负责学习研究、私人知识和内容系统。短帖、Thread、GitHub 项目介绍与文章由现有写作 Skills 完成；图片、GIF、视频、音频与播客制作，普通翻译、广告投放、销售页、邮件营销、品牌全案、完整营销策略和实际发布也不在这三个入口的交付范围内。

文件写入、媒体制作、上传和发布互不代替。没有明确授权时，结果只保留在当前回复或本地工作区。

## 项目结构与维护

```text
100x-learning/
├── skills/
│   ├── 100x-learning/         # 材料理解、研究、解释、实践与长材料
│   ├── private-knowledge/     # 私人库、知识沉淀、健康检查与 Marktree
│   └── content-system/        # 策略、选题、复盘、案例、钩子与写作记忆
├── assets/readme/             # GitHub 主页视觉素材
├── tests/                     # 跨 Skill 行为、生产消费链和资源边界测试
└── archive/                   # 已退休资料，不参与当前运行
```

每个 `skills/<name>/SKILL.md` 都是独立入口，并只读取自己职责内的 reference 与脚本。`private-knowledge` 提供唯一私人库合同，其它入口通过正式脚本消费；`archive/` 中的旧路径不会参与当前运行。

维护脚本使用 Python 标准库。完整行为测试：

```bash
python -m pytest -q
```

贡献前请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。行为细节、脚本入口和各条方法以 [skills/](./skills/) 下的活动入口及其 reference 为准，README 不维护第二套内部规则。

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>

## 许可证

仓库原创的 Skill 指令、源码、测试、脚本和可复用模板采用 [Mozilla Public License 2.0](./LICENSE)。`archive/`、`output/`、导入的案例、来源文章、社交帖子、截图及其它第三方或参考内容不在这项授权范围内；完整边界见 [LICENSING.md](./LICENSING.md)。
