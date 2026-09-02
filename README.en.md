<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>Turn sources, topics, and real problems into knowledge you can understand, evaluate, and apply.</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <strong>English</strong> · <a href="./README.ja.md">日本語</a> | <a href="./SKILL.md">Docs</a> | <a href="./CONTRIBUTING.md">Contributing</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">Issues</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X: @0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram: CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="Blog: blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="Homepage: blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/100x-learning/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/100x-learning?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/100x-learning/forks"><img src="https://img.shields.io/github/forks/CheshireMew/100x-learning?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/100x-learning/blob/main/LICENSING.md"><img src="https://img.shields.io/github/license/CheshireMew/100x-learning?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

`100x-learning` is a learning and research Skill built to the open [Agent Skills specification](https://agentskills.io/specification). It reads sources, transcripts, links, topics, and real problems, then selects the method that matches the requested outcome: understanding, research, explanation, practice, or durable knowledge capture.

<p align="center">
  <img src="./assets/readme/hero-en.png" width="100%" alt="How 100x Learning turns materials, topics, and real questions into understanding, judgment, and application">
</p>

## Example requests

- **Understand a source:** `Explain what this document actually establishes. Separate direct evidence, reasonable inference, and unknowns.`
- **Research and verify:** `Verify these claims online, prefer contemporary primary sources, and explain conflicts between sources.`
- **Explain a concept:** `Explain the high-water mark with a concrete example, then give the precise definition and limits.`
- **Apply knowledge:** `Use this framework on my case and identify assumptions, observable results, and the next test.`
- **Clean a transcript:** `Remove mechanical subtitle formatting and confirmed transcription errors while preserving meaning, order, and complete content.`
- **Capture knowledge:** `Save the verified sources and conclusions from this task to my configured private library.`

The Skill stops at the requested outcome. Research does not automatically become a long-running project, transcripts do not automatically become summaries, selected excerpts do not become media deliverables, and the private library is not changed without write authorization.

## Capabilities

| Goal | Method | Outcome |
| --- | --- | --- |
| Understand sources | Identify claims, evidence, relationships, conditions, and gaps | A traceable explanation |
| Research topics | Open primary sources and check context and time scope | Facts, inferences, opinions, and unknowns kept separate |
| Explain concepts | Start from a real problem, mechanism, and example; retain formal anchors | An explanation usable in the current situation |
| Practice | Map knowledge to goals, actions, indicators, and feedback | A plan, tool, judgment, or review |
| Ingest sources | Read video, social, transcript, and key-frame context | A traceable source package |
| Normalize transcripts | Remove mechanical formatting and confirmed noise without compressing content | A faithful, continuous source text |
| Maintain a private library | Initialize, adopt, query, validate, and inspect health | Durable local knowledge |

Articles, posts, and existing drafts may be inputs for comprehension, research, or fact-checking. This Skill does not create publishable content, continue or polish drafts, review prose style, operate topic pipelines, maintain case or hook libraries, model an author voice, or review publication performance.

## Private knowledge library

The user chooses a local directory. Private content is never stored in this repository:

```powershell
python scripts/private_library.py init --root "D:\Knowledge\My Library"
python scripts/private_library.py show
python scripts/private_library.py validate
python scripts/private_library_health.py
```

Use `adopt --root <path>` for an existing compatible library. The config stores only the version and root path. `init` does not overwrite a non-empty directory, and `adopt` does not move or rewrite existing knowledge. Inactive directories left by older versions are preserved and ignored rather than deleted, migrated, initialized, or validated.

Active directories are `00-Inbox`, `10-Knowledge`, `20-Sources`, `30-Projects`, `40-Outputs`, `50-Areas`, `60-Systems`, and `90-Archive`.

## Installation and compatibility

Clone or copy the repository into the skills directory of an Agent Skills-compatible host, then invoke `$100x-learning` in your request. The exact loading path depends on the host. The private library remains separate from the Skill source.

The Python utilities use the standard library. Automated acceptance currently targets Windows.

## Repository layout

```text
100x-learning/
├── SKILL.md                   # Entry point and boundaries
├── agents/openai.yaml         # Client-facing metadata
├── references/                # Learning, research, practice, and library methods
├── scripts/                   # Transcript, source, and private-library tools
├── assets/private-library/    # Generic templates for a new private library
├── tests/                     # Behavioral and script tests
└── archive/                   # Historical files for retired capabilities
```

## License

See [LICENSING.md](./LICENSING.md) for the boundary between code, original documentation, and third-party materials.
