<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>把材料、主题和真实问题变成能理解、判断和使用的知识。</strong>
</p>

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

`100x-learning` 是一个遵循 [Agent Skills 开放格式](https://agentskills.io/specification)的学习与研究 Skill。它读取材料、字幕、链接、主题和真实问题，按用户要达到的结果选择理解、研究、解释、实践或知识沉淀方法。

<p align="center">
  <img src="./assets/readme/hero.png" width="100%" alt="材料、主题和真实问题经过 100x Learning 形成理解、判断和使用结果的机制图">
</p>

## 可以直接这样使用

- **读懂材料**：`解释这份文件真正规定了什么，分开原文事实、合理推断和仍不知道的部分。`
- **研究与核查**：`联网核查这些说法，优先找同期原始资料，并说明来源冲突。`
- **解释概念**：`用一个具体例子解释高水位线，再补充准确的技术定义和适用边界。`
- **用于真实问题**：`把这个框架用于我的案例，列出假设、可观察结果和下一次验证。`
- **整理字幕**：`清理字幕格式和可确认的转录错误，保留原意与顺序，整理成连续可读的完整来源。`
- **沉淀知识**：`把本次确认过的来源和结论写入已配置的私人知识库。`

Skill 会停在用户指定的结果。研究不会自动变成长期项目，字幕不会自动变成摘要，候选片段不会自动变成媒体成品，未得到写入授权时也不会修改私人知识库。

## 核心能力

| 目标 | 处理方式 | 结果 |
| --- | --- | --- |
| 理解材料 | 找主张、证据、关系、条件与缺口 | 可复核的材料解释 |
| 研究主题 | 搜索原始资料，核对上下文和时间口径 | 事实、推断、观点与未知分开的结论 |
| 解释概念 | 从现实问题、机制和例子进入，再保留正式定义 | 能理解并用于当前问题的解释 |
| 实践应用 | 把知识映射到目标、动作、指标和反馈 | 方案、工具、判断或复盘 |
| 来源接入 | 读取视频、社交内容、字幕与关键画面 | 可追溯的来源包 |
| 字幕整理 | 清除机械格式与可确认噪音，保留完整内容 | 忠实、连续、可读的来源全文 |
| 私人知识库 | 初始化、接入、查询和健康检查 | 本机可持续使用的知识结构 |

材料、文章、帖子和现成草稿都可以作为理解、研究或事实核查的输入，但本 Skill 不负责内容创作、续写、改写润色、文风审查、选题运营、案例钩子、作者声音或发布复盘。

## 私人知识库

私人库由用户主动选择本机目录，仓库本身不包含私人内容：

```powershell
python scripts/private_library.py init --root "D:\Knowledge\My Library"
python scripts/private_library.py show
python scripts/private_library.py validate
python scripts/private_library_health.py
```

已有符合结构的目录可以使用 `adopt --root <path>` 接入。配置文件只保存库版本和路径；`init` 不覆盖非空目录，`adopt` 不移动或改写现有知识。旧版本可能留下非活动目录，当前 Skill 会忽略并保留它们，不自动删除、迁移、初始化或验证。

活动结构包括：

```text
00-Inbox/       临时入口
10-Knowledge/   同主题唯一活动知识
20-Sources/     原始来源
30-Projects/    有结束条件的任务
40-Outputs/     研究、实践和其它确认成果
50-Areas/       持续责任
60-Systems/     稳定流程、模板和规则
90-Archive/     退出活动范围的历史内容
```

## 安装与兼容

把仓库克隆或复制到支持 Agent Skills 的客户端技能目录，并在请求中点名 `$100x-learning`。具体目录和加载方式由宿主决定；本项目不要求私人库与 Skill 源码放在一起。

项目中的 Python 脚本使用标准库即可运行。当前自动化测试以 Windows 环境为主要验收平台。

## 仓库结构

```text
100x-learning/
├── SKILL.md                   # 能力入口与边界
├── agents/openai.yaml         # 客户端展示信息
├── references/                # 学习、研究、实践与知识库方法
├── scripts/                   # 字幕、来源和私人知识库工具
├── assets/private-library/    # 新建私人库使用的通用模板
├── tests/                     # 行为与脚本测试
└── archive/                   # 已退出能力的历史文件
```

## 许可

代码与原创文档的许可边界见 [LICENSING.md](./LICENSING.md)。第三方材料、商标和外部资源仍受其各自条款约束。
