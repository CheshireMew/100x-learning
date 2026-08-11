# 完整内容案例库

用于用户明确要求时保存、更新和维护完整案例。案例库不管理钩子，也不直接参与普通写作；活动案例只作为重新蒸馏和验证写作模板的原始语料。

## 存储与索引

完整社交内容位于 `<私人知识库>/20-Sources/Social Posts/Content Cases/完整社交内容/`，统一保存独立短帖和 Thread；文章案例位于 `<私人知识库>/20-Sources/Articles/Content Cases/`。活动索引分别是：

```text
<私人知识库>/20-Sources/Content Cases/社交内容案例索引.md
<私人知识库>/20-Sources/Content Cases/文章案例索引.md
```

索引按可迁移的写作技巧组织，不按对象、题材、行业或任务分类。稳定 `case_id` 用于找到原文；索引和文件名不需要暴露题材标题。独立短帖和 Thread 不再区分，统一作为社交内容；文章继续单独保存，避免文章篇幅反过来规定社交内容。

## 创建和更新

只有用户明确要求保存或更新案例时才写入。保存未经改写的完整正文；独立短帖和 Thread 都使用 `social`，文章使用 `article`。写入活动目录前阅读全文，确认它值得作为模板研究证据：事实关系清楚、信息量与篇幅相称、没有翻译腔和空泛总结，并且所记录的写作技巧脱离题材仍可学习。

原始笔记、链接堆叠、规格清单、松散转录、通用宣传稿、反复宣布重要性、靠空泛总结收尾，以及已经被真实成品证明会放大模板感或篇幅的案例不进入活动目录。不能确认质量时保留为候选材料。活动案例持续污染真实成品时，重新阅读全文；确认后移到活动目录之外的可回查归档并重建索引，不把筛选理由写进案例正文或创作输入。

```powershell
python scripts/content_case_library.py add-case --kind social --input "完整原文.md" --title "案例标题" --technique "结果先行"
python scripts/content_case_library.py build-index
python scripts/content_case_library.py validate
```

案例需要同时进入写作记忆时，通过 `--writing-format`、`--writing-purpose`、`--writing-origin` 和 `--voice-eligible` 明确相应字段；这些字段不进入普通案例索引。更新已有资源时修改唯一案例文件并重建索引。

## 通过标准

- 案例脚本、目录与索引只区分社交内容和文章；社交内容不再区分独立短帖与 Thread，且案例库不读取钩子库。
- 活动案例保存完整原文、稳定寻址字段和必要写作技巧，不保存题材检索字段，也不直接进入普通成文输入。
- 归档内容不会进入活动索引。
