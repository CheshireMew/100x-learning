---
name: 100x-learning
description: 帮助用户读懂材料、研究主题、解释概念，并把知识用于真实问题；也处理长材料、视频和社交来源。适用于划重点、系统学习、比较来源、事实核查、实践应用和分轮完成大型学习任务；内容策略、私人知识库维护与可发布文字由对应的独立 Skill 完成。
---

# 100x Learning

## 目标

把材料、陌生主题或真实问题变成用户现在能理解、判断和使用的结果。资料已经足够时直接完成，不把简单问题扩成研究项目；用户只要解释、研究或实践中的一项时，在该结果完成后停止。

本 Skill 负责材料理解、主题研究、概念解释、学习方法、实际应用和可恢复的长材料项目。值得分享的内容选择、长期内容策略和发布复盘由 `$content-system` 完成；私人知识库的初始化、接入、保存和检查由 `$private-knowledge` 完成；重新创作可发布文字使用 `$prep-this` 与 `$write-this`，已有成稿检查使用 `$clean-copy`。

## 正常工作

先完整理解用户的自然语言要求、当前材料和最终用途。根据当前卡点选择最低充分的方法，不把来源、深度或输出形式预先变成互斥路线：

- 判断怎样学或为什么卡住时读取 `references/learning-process-and-method-selection.md`。
- 阅读文章、字幕、课程、访谈和其它长材料时读取 `references/material-analysis.md`。
- 用户只给出主题、要求比较来源、核查重要事实或补足研究时读取 `references/research-led-learning.md`；已经接入私人库并且旧知识可能有用时同时读取 `references/research-context-reuse.md`。
- 解释概念读取 `references/concept-deconstruction.md`；系统学习读取 `references/continuous-learning.md`；把知识用于真实问题读取 `references/practice-led-learning.md`。
- 视频、社交帖子和 Thread 先按 `references/source-ingestion.md` 取得可靠正文、时间位置、关键画面和来源身份，再直接用于当前结果。

同一请求明确包含理解、研究和实践等多个结果时按真实依赖连续完成。用户只附材料或只点名本 Skill 而没有指定产物时，直接讲清材料本身。默认使用中文；只有准确搜索、操作或官方名称需要时保留必要外文。

## 私人知识与后续结果

普通学习不要求私人知识库。研究前确实需要复用已有知识时，使用兄弟 Skill 的正式入口取得唯一根目录：

```text
python <private-knowledge-skill>/scripts/private_library.py show
```

配置不存在或路径不可用时继续使用当前材料和外部来源，不临时建库。用户明确要求把本次结果保存、更新或沉淀时，先完成当前学习结果，再由 `$private-knowledge` 按其正式写入规则保存；本 Skill 不复制知识库目录、索引和写入规则。

用户进一步要求把学习结果变成内容方向、分享候选或发布复盘时，把当前材料和已经形成的认识原样交给 `$content-system`。要求写成短帖、Thread、项目介绍或文章时，把用户原话、来源和当前研究结果作为写作材料交给现有写作入口，不把研究过程改写成另一份创作简报。

## 长材料和字幕

一份材料能够在当前任务完成时直接处理。只有材料确实无法可靠一次完成、单元处理成本较高，或用户明确要求分轮继续时，才读取 `references/durable-learning-projects.md`，并使用：

```text
python <100x-learning-skill>/scripts/durable_learning_project.py
```

项目根必须是用户明确给出的工作区；清单、单元输出和汇总都属于该项目，不写进 Skill 源码。处理本地 SRT、VTT、带时间戳 TXT 或断行严重的字幕时使用：

```text
python <100x-learning-skill>/scripts/normalize_subtitles.py
```

规范化结果写到用户指定位置，保留原文件和真实时间信息。

## 完成

第一段直接回答用户真正的问题。材料范围、事实与推断、关键关系、会改变判断的边界和用户指定的格式保持准确；能够客观核实的结果使用真实来源、程序状态或实际产物判断。当前结果已经足以支持理解、判断或行动时停止，不自动增加保存、写作、发布或内容规划。
