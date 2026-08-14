---
name: private-knowledge
description: 初始化、接入、读取、整理、检查和维护本机私人知识库，并为学习、研究与内容系统提供唯一的知识、来源、项目、成果和路径真源。适用于知识沉淀、批量接入、库健康检查和 Marktree 协作；普通解释、写作与内容策略由对应 Skill 完成。
---

# Private Knowledge

## 目标

让用户的私人知识、来源、项目、成果和长期系统保存在一个可定位、可继续使用的本机知识库中。本 Skill 负责知识库的目录合同、唯一根目录、读写落点、主题合并、批量接入、健康检查和可选 Marktree 协作；它不替代学习研究、内容策略或成文。

私人库独立于 Skill 源码。所有脚本都使用当前 Skill 目录中的正式入口，不根据终端当前目录猜路径。初始化、接入或写入前完整读取 `references/private-knowledge-library.md`。

## 初始化、接入与定位

用户明确给出新库位置时运行：

```text
python <private-knowledge-skill>/scripts/private_library.py init --root <absolute-path>
```

用户指定已有库时运行 `adopt`。没有给位置且当前结果必须落到本机时，只询问保存位置。目标已有其它内容但没有私人库标识时停止，不覆盖或搬动现有内容。

正常读取、写入和其它 Skill 需要私人库时统一运行：

```text
python <private-knowledge-skill>/scripts/private_library.py show
```

`show` 返回的 `library_root` 是本次唯一根目录。默认配置继续保存在当前用户的 `.100x-learning/config.json`，从而让已有私人库无需迁移就能继续使用。缺少配置时只停止依赖私人库的结果，不影响其它 Skill 使用当前材料继续工作。

## 读取与沉淀

需要读取或写入长期知识时完整读取 `references/knowledge-base-workflow.md`。先读私人库的 `Home.md`，再按真实主题和别名找到唯一活动文档；来源、知识、项目、成果和系统按各自职责保存，不把同一正文复制成多份活动真源。

用户明确要求保存、整理、更新或沉淀时才写入。先保留来源身份、原文边界和必要上下文，再把稳定概念、机制、证据判断、限制和开放问题合并进对应主题。一次学习、研究或内容任务已经形成的结果作为输入使用，不重新执行原任务。

大批量接入前读取 `references/bulk-knowledge-ingestion.md`。批量工作会产生大量文件时，真正执行前展示来源范围、单元划分、目标目录、产物数量和验收方式并等待确认；普通单文件写入不增加这道门槛。

## 内容资源与 Marktree

私人库同时保存由 `$content-system` 维护的完整案例、独立钩子、发布记录和内容策略，但这些内容的选择、复盘和维护判断仍由 `$content-system` 负责。本 Skill 只提供目录、路径、写入和一致性基础。

用户已经配置 Marktree CLI 时，按 `references/private-knowledge-library.md` 连接同一个真实根目录，并通过：

```text
python <private-knowledge-skill>/scripts/marktree_integration.py
```

执行受管写入和状态核对。未配置时保持独立文件工作流，不阻断知识库操作；只有用户明确要求同步远端时才执行外部同步。

## 健康检查

用户要求检查或维护知识库时完整读取 `references/knowledge-base-health.md`，再运行：

```text
python <private-knowledge-skill>/scripts/private_library_health.py
```

健康检查读取同一私人库中的知识、链接、案例、钩子和写作记忆，并区分错误、警告和建议。默认只报告真实问题；用户明确要求修复时才修改相应正式文件，修复后重新运行检查。

## 完成

初始化或接入完成时说明实际根目录、本机配置和验证结果；写入时说明更新了哪些正式文件与认识；健康检查时说明真实问题及影响。完成前重新读取实际文件，并让正式脚本从本机配置再次定位同一个库。目录存在只证明结构，真实材料已经进入唯一正式位置并能被下一次读取后，才说明相应知识结果已保存。
