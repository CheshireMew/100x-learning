# 内容案例检索

用于在 100x Learning 成文前，为当前交付形态和内容类型取得可直接阅读全文的示范。完整案例是写作生产者的正式输入：模板告诉 Agent 这类内容需要完成什么，案例让 Agent 看见这些职责怎样通过开头、推进、密度、节奏和收束成为一篇自然正文。

## 一、活动案例库

唯一活动入口是：

~~~text
System Knowledge/20-Sources/Content Cases/内容案例索引.md
~~~

索引按成品形态分为：

- **钩子与开头**：展示开头怎样建立结果、冲突、问题或反差。
- **完整短内容**：服务短帖、Thread、项目短介绍和短文案。
- **完整文章**：服务文章与 Newsletter。

正文案例再按项目与产品介绍、概念与机制解释、教程与操作指南、清单与资源推荐、事件与商业故事、观点与趋势判断、行业与投资分析、个人观察与实测等内容类型组织。每条案例在本地保存全文、可以参考什么、适用场景和来源链接；文章另外记录来源性质。

## 二、形成检索条件

从当前 writing_job 和内容真源提取：

1. **写作任务**：这篇文字实际要完成什么。
2. **内容类型**：项目介绍、机制解释、教程、清单、故事、观点、分析或个人实测中的哪一类。
3. **主题**：对象、领域和会影响匹配的关键概念。
4. **结构**：当前需要的推进关系，例如具体结果、操作过程、因果、对比、数量推演或作者判断。

交付形态决定正文资产：

- short_post、thread、short_copy 和 github_project_short 使用 short。
- article 和 newsletter 使用 article。
- 用户明确要求病毒式传播时，在正文资产之外同时使用 hook。

每次起草、结构调整和文字修改都让模板与同类型完整正文案例同时进入写作输入。对象、内容类型、交付形态或整篇推进发生变化时，用新条件重新检索。

## 三、执行检索并取得全文

在 Skill 根目录运行：

~~~powershell
python scripts/content_case_library.py search --writing-task "介绍开源项目" --content-type "项目与产品介绍" --topic "视频自动化" --structure "用户结果" --asset short --limit 3
~~~

病毒式传播任务示例：

~~~powershell
python scripts/content_case_library.py search --writing-task "介绍开源项目" --content-type "项目与产品介绍" --topic "视频自动化" --structure "用户结果" --asset hook --asset short --limit 3
~~~

文章把正文资产改为 article。--topic、--structure 和 --asset 可以重复。检索器先锁定正文内容类型，再按写作任务、主题和结构排序；每种请求资产至少返回一条可读取案例，并直接输出全文、说明、适用场景和来源。

案例库缺少当前内容类型或交付形态所需资产时，先补齐经过来源确认的同类型案例，或请用户提供可作为当前运行资源的同类全文，再进入成文。完整正文案例是生产输入的一部分，钩子、模板和抽象技巧都不替代它。

## 四、把完整案例交给同一个生产者

把选中的本地路径写入 writing_examples.references，并保留本次 writing_task、content_type、topics 和 structure。当前 Agent 同时读取：

~~~text
内容真源
当前作者声音的真实来源
交付形态对应的模板全文
同内容类型的正文案例全文
用户明确要求病毒式传播时的开头案例全文
~~~

案例全文负责展示：

- 开头怎样让具体结果、问题或冲突出现。
- 后续段落怎样兑现开头。
- 信息怎样逐步增加并保持自然推进。
- 作者判断怎样从事实中长出来。
- 句长、停顿、重复、列表和段落怎样形成节奏。
- 结尾怎样完成判断、入口、行动或余味。

“可以参考什么”和“适用场景”帮助 Agent 看懂案例机制，全文保留这些机制之间的连接。生产者直接使用完整案例，不把它先压缩成少数标签再写。当前内容真源继续决定人物、事实、产品、数字、经历和结论；当前作者声音继续决定新正文的措辞、节奏、判断强度和完成度。

## 五、通过标准

- 模板与同类型完整正文案例已经进入同一个写作输入。
- 短内容读取 short 全文，文章和 Newsletter 读取 article 全文。
- 用户明确要求病毒式传播时，正文案例与 hook 全文同时存在。
- GitHub 项目短介绍的正文案例属于“项目与产品介绍”。
- 案例路径能够由 harness.content_cases.parse_case 读取，正文、说明、适用场景和来源完整。
- 最终正文使用当前事实和作者声音，同时能观察到案例展示的开头、推进、密度、节奏或收束机制。
- writing_examples 字段和检索标签留在内部，用户直接得到自然正文。

validate-writing 检查模板路径、完整案例路径、正文资产、内容类型、作者声音来源和内容真源是否共同存在。正文质量由当前 Agent 对照真实资源完成语义检查。

## 六、维护案例库

博客出现新文章或正文更新时，先在 blog-article-decisions.json 为新增文章明确填写来源性质、参考去向、内容类型和判断依据，再同步正文并重建唯一索引：

~~~powershell
python scripts/sync_blog_articles.py sync
python scripts/sync_blog_articles.py validate
python scripts/content_case_library.py build-index
python scripts/content_case_library.py build-index --check
~~~

blog-article-decisions.json 是人工复核和同步流程共同使用的唯一判定源。新内容完成来源性质和参考价值复核后进入活动案例库。需要退出活动范围的旧正文或索引按项目规则移入 90-Archive。
