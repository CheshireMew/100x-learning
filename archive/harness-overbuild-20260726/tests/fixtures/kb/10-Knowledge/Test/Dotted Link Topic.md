---
type: knowledge-note
status: active
created: 2026-07-16
updated: 2026-07-16
topic: dotted-link-topic
aliases:
  - Dotted Link Alias
---

# Dotted Link Topic

This note verifies that full-path Obsidian links remain resolvable when the target filename contains a dot.

## Current understanding

The extensionless link [[20-Sources/Test/Source.v1|dotted source]] should resolve to `Source.v1.md` instead of replacing `.v1` with `.md`.

## Sources

The linked fixture is the source used by this deterministic test.

## Boundaries

This statement applies only to dotted Markdown filenames inside the fixture knowledge base.

