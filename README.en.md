<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>Give learning, private knowledge, and content improvement clear, composable entry points.</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong> · <a href="./README.ja.md">日本語</a> | <a href="./skills/100x-learning/SKILL.md">Docs</a> | <a href="./CONTRIBUTING.md">Contributing</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">Issues</a>
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

`100x-learning` is a multi-Skill repository built to the open [Agent Skills specification](https://agentskills.io/specification). Its three entry points share one durable resource contract while separately handling learning, private knowledge, and content-system work.

<p align="center">
  <img src="./assets/readme/hero-en.png" width="100%" alt="How 100x Learning turns materials, topics, and real questions into insight, decisions, action, and shareable work">
</p>

## Start with the result you want

You do not need to choose an internal workflow. Describe the outcome directly:

- **Understand a source**: `Explain the main thread and key relationships in this interview, and mark the passages worth revisiting.`
- **Research and decide**: `Research X, compare whether A or B better fits my goal, and keep the unknowns visible.`
- **Explain and apply**: `Explain X through a real scenario, then use it to analyze the Y I am facing.`
- **Continue learning**: `Teach me X over multiple rounds. Finish the most useful lesson now, then use my feedback to choose the next step.`
- **Capture knowledge**: `Use $private-knowledge to save these conclusions and update the existing source of truth.`
- **Improve content**: `Use $content-system to review this published piece and decide what the next piece should test.`

Each Skill stops at its own result: learning does not save automatically, a shareable candidate does not become a post, and one review does not rewrite long-term strategy. Publishable writing remains with `prep-this`, `write-this`, and `clean-copy`.

## Quick start

Install the complete repository with an Agent Skills-compatible installer:

```bash
npx skills add CheshireMew/100x-learning
```

The installer discovers `100x-learning`, `private-knowledge`, and `content-system`. You can also clone the repository and install the required entries from `skills/`.

After installation, describe the result directly:

```text
Read this material. First explain the content, main thread, and key relationships faithfully.
Then tell me which parts are most worth investigating further.
```

Hosts that support explicit names can use `$100x-learning`, `$private-knowledge`, or `$content-system`.

## How it stays on target

| Your request | What the Skill does | Delivery and stopping point |
| --- | --- | --- |
| Understand a source | Reconstructs the content, main thread, relationships, and real locations faithfully | A clear explanation and highlights, without expanding into a research project |
| Research or verify | Compares sources and separates facts, judgments, and unknowns | A sourced conclusion and the questions still open |
| Save or check knowledge | Resolves, writes, and verifies one configured private library | Durable knowledge and its real status |
| Select shareable material | Understands the complete source before choosing for audience and purpose | Candidates and reasons, without drafting |
| Review published content | Separates observed results, explanations, and alternatives | The next testable content decision |

One-off tasks do not require a persistent system. Durable material is used only when you explicitly request maintained content direction, saved results, history, or personal voice.

## Optional: private knowledge library and ongoing work

The private knowledge library lives outside the Skill directory and is never distributed with the public repository. Ask the Agent to initialize a new library or adopt an existing Markdown library:

```text
Use $private-knowledge to initialize my private knowledge library at D:\Knowledge\100x-learning.
Use $private-knowledge to adopt my existing private knowledge library at E:\Knowledge\Existing Library.
```

The selected root is recorded in `~/.100x-learning/config.json`; the config stores only the library version and path, not private text. `init` will not overwrite a non-empty directory. `adopt` adds the project marker and updates the local pointer without moving or rewriting existing knowledge.

Once connected, `private-knowledge` owns sources, topic knowledge, projects, and outputs. `content-system` uses the same library for cases, hooks, publication records, content direction, and durable topic state. Neither creates a second data root.

<details>
<summary>Run the knowledge-library maintenance scripts directly</summary>

```powershell
python skills/private-knowledge/scripts/private_library.py init --root "D:\Knowledge\100x-learning"
python skills/private-knowledge/scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
python skills/private-knowledge/scripts/private_library.py show
python skills/private-knowledge/scripts/private_library.py validate
```

</details>

Without a configured library, source comprehension, research, shareable selection, and current-response content decisions still work. Cloning the public repository never includes private material.

## Scope

This repository covers learning and research, private knowledge, and content-system work. Existing writing Skills handle posts, threads, GitHub project introductions, and articles.

Image, GIF, video, audio, and podcast production; general translation; ad buying; sales pages; email sequences; full brand or marketing strategy; and publishing itself belong to separate capabilities.

Writing a file, producing media, uploading, and publishing are different actions. Without explicit authorization, results remain in the current response or local workspace.

## Repository structure and maintenance

```text
100x-learning/
├── skills/
│   ├── 100x-learning/         # Learning, research, explanation, practice, long materials
│   ├── private-knowledge/     # Private library, durable knowledge, health, Marktree
│   └── content-system/        # Strategy, topics, reviews, cases, hooks, writing memory
├── assets/readme/             # GitHub README visuals
├── tests/                     # Cross-Skill behavior and producer-consumer tests
└── archive/                   # Retired material; never loaded by the active runtime
```

Each `skills/<name>/SKILL.md` is an independent entry point. `private-knowledge` owns the single library contract consumed by the other entries. Retired paths in `archive/` are not part of the current runtime.

Maintenance scripts use the Python standard library. Run the complete behavior suite with:

```bash
python -m pytest -q
```

Read [CONTRIBUTING.md](./CONTRIBUTING.md) before contributing. Behavior and script entry points live under [skills/](./skills/); the README does not maintain a second copy of the internal rules.

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>

## License

Original Skill instructions, source code, tests, scripts, and reusable templates are licensed under the [Mozilla Public License 2.0](./LICENSE). `archive/`, `output/`, imported cases, source articles, social posts, screenshots, and other third-party or reference material are outside that grant. See [LICENSING.md](./LICENSING.md) for the exact scope.
