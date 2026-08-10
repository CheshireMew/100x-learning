<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/hero-en.png" width="100%" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>Turn sources, topics, and real problems into work you can understand, evaluate, apply, or share.</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong> · <a href="./README.ja.md">日本語</a> | <a href="./SKILL.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">反馈</a>
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

`100x-learning` is a learning and content Skill built to the open [Agent Skills specification](https://agentskills.io/specification). It reads subtitles, articles, links, topics, projects, drafts, and post-publication feedback, then chooses the method that matches the result you asked for. It is not a standalone app or tied to one Agent host.

## Start with the result you want

You do not need to choose an internal workflow. Describe the outcome directly:

- **Understand a source**: `Explain the main thread and key relationships in this interview, and mark the passages worth revisiting.`
- **Research and decide**: `Research X, compare whether A or B better fits my goal, and keep the unknowns visible.`
- **Explain and apply**: `Explain X through a real scenario, then use it to analyze the Y I am facing.`
- **Review or write**: `Check this draft for factual, structural, and AI-sounding problems. Do not rewrite it.` or `Turn these materials into a thread for general readers.`
- **Learn and improve continuously**: `Teach me X over multiple rounds. Finish the most useful lesson now, then use my feedback to choose the next step.`
- **Capture knowledge**: `Save the confirmed conclusions to my private knowledge library and update the existing source of truth for this topic.`

The Skill stops at the result you named: a review does not silently rewrite the draft, candidates do not silently become a post, and one topic-selection task does not become a long-running project. Saving files, producing media, uploading, and publishing are separate actions.

## Quick start

Place the complete repository in a Skills directory read by a compatible Agent. Tools that support project-level `.agents/skills/` can use:

```bash
git clone https://github.com/CheshireMew/100x-learning.git .agents/skills/100x-learning
```

If your tool uses a user-level directory or another location, replace the destination with its Skills directory. Discovery paths and explicit invocation syntax are host-specific; the [official quickstart](https://agentskills.io/skill-creation/quickstart) shows the project-level layout.

After installation, describe the result directly:

```text
Read this material. First explain the content, main thread, and key relationships faithfully.
Then tell me which parts are most worth investigating further.
```

Hosts that support explicit Skill names can also use `$100x-learning`. The first successful result should be a clear explanation of the source itself—not generic study advice or a description of the internal workflow.

## How it stays on target

| Your request | What the Skill does | Delivery and stopping point |
| --- | --- | --- |
| Understand a source | Reconstructs the content, main thread, relationships, and real locations faithfully | A clear explanation and highlights, without expanding into a research project |
| Research or verify | Compares sources and separates facts, judgments, and unknowns | A sourced conclusion and the questions still open |
| Review content | Checks facts, structure, language, and the requested concerns | Problems and revision direction, without silently editing the draft |
| Write content | Organizes the supplied material, supplements it from the web when useful, then drafts directly | A usable post, thread, GitHub project introduction, or article |
| Continue learning or review results | Reads the real artifact, feedback, and outcome from the current round | The next lesson, topic, or testable improvement |

Web supplementation for writing adds useful material; it is not automatically a claim-by-claim fact-check. Research, source comparison, or verification becomes the deliverable only when you explicitly ask for it.

In normal mode, sufficient material leads directly to the finished artifact. If the host provides a Plan mode, you can use it for a deeper interview: the Skill first gathers information it can obtain independently, then asks for the experiences, emotions, views, and disclosure boundaries only you can provide.

One-off tasks do not require a persistent system. The Skill uses durable material only when you explicitly ask for continuous learning, a maintained content direction, saved results, or personal voice.

## Optional: private knowledge library and ongoing work

The private knowledge library lives outside the Skill directory and is never distributed with the public repository. Ask the Agent to initialize a new library or adopt an existing Markdown library:

```text
Use $100x-learning to initialize my private knowledge library at D:\Knowledge\100x-learning.
Use $100x-learning to adopt my existing private knowledge library at E:\Knowledge\Existing Library.
```

The selected root is recorded in `~/.100x-learning/config.json`; the config stores only the library version and path, not private text. `init` will not overwrite a non-empty directory. `adopt` adds the project marker and updates the local pointer without moving or rewriting existing knowledge.

Once connected, the library can hold sources, one source of truth per topic, complete writing cases, independent hooks, confirmed work, content direction, and durable topic state.

Ordinary writing reads only cases and hooks; it does not automatically bring topic knowledge, personal voice, or publication history into a new draft. Those materials are used only when you explicitly request the corresponding result. A single publication outcome does not rewrite long-term strategy or personal voice.

<details>
<summary>Run the knowledge-library maintenance scripts directly</summary>

```powershell
python scripts/private_library.py init --root "D:\Knowledge\100x-learning"
python scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
python scripts/private_library.py show
python scripts/private_library.py validate
```

</details>

Without a configured library, source comprehension, research, review, and writing still work from the current input. Cloning the public repository never includes private material.

## Scope

This Skill covers source comprehension, topic research, concept explanation, practice design, content review, short posts, threads, GitHub project introductions, and articles.

Image, GIF, video, audio, and podcast production; general translation; ad buying; sales pages; email sequences; full brand or marketing strategy; and publishing itself belong to separate capabilities.

Writing a file, producing media, uploading, and publishing are different actions. Without explicit authorization, results remain in the current response or local workspace.

## Repository structure and maintenance

```text
100x-learning/
├── SKILL.md                   # Main routing, behavior boundaries, and delivery rules
├── agents/openai.yaml         # Presentation and default prompt for OpenAI hosts
├── references/                # Learning, research, writing, and knowledge-library methods
├── scripts/                   # Subtitle, private-library, case, hook, and writing-memory tools
├── assets/private-library/    # Public templates used to initialize a private library
├── assets/readme/             # GitHub README visuals
├── tests/                     # Behavior, producer-consumer chain, and resource-boundary tests
└── archive/                   # Retired material; never loaded by the active runtime
```

`SKILL.md` is the single entry point, `references/` owns the specialized methods, and `scripts/` provides deterministic maintenance operations. `agents/openai.yaml` adapts presentation for one host without changing the project’s identity as a general Agent Skill. Retired paths in `archive/` are not part of the current runtime.

Maintenance scripts use the Python standard library. Run the complete behavior suite with:

```bash
python -m unittest discover -s tests -v
```

Read [CONTRIBUTING.md](./CONTRIBUTING.md) before contributing. Behavior details, script entry points, and specialized methods live in [SKILL.md](./SKILL.md) and its active references; the README does not maintain a second copy of the internal rules.

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>

## License

Original Skill instructions, source code, tests, scripts, and reusable templates are licensed under the [Mozilla Public License 2.0](./LICENSE). `archive/`, `output/`, imported cases, source articles, social posts, screenshots, and other third-party or reference material are outside that grant. See [LICENSING.md](./LICENSING.md) for the exact scope.
