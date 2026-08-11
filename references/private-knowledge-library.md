# 私人知识库初始化与定位

用于初始化新的私人知识库、接入已有知识库，以及在知识、案例、钩子和写作记忆流程开始前取得唯一根目录。本文件只负责根目录和冷启动，不决定材料应该沉淀成什么。

## 初始化新库

用户可以直接说：

```text
使用 $100x-learning 初始化私人知识库，位置是 D:\Knowledge\100x-learning。
```

显式调用语法由 Agent 宿主决定；没有 `$skill-name` 语法时，直接用自然语言表达同一目标即可。用户明确要求初始化并给出保存位置时运行：

```powershell
python scripts/private_library.py init --root "D:\Knowledge\100x-learning"
```

没有给保存位置时只询问这一项。新库必须位于 Skill 目录之外。初始化器会分别建立完整案例库与独立钩子库，以及 `Home.md`、知识、来源、成果、写作系统和归档目录；两类参考使用不同脚本和索引。写作系统包含未配置的长期内容策略，以及持续选题和发布复盘模板。它不会根据空白库推测用户定位。唯一根目录记录到当前用户的 `~/.100x-learning/config.json`。目标目录已经包含其它内容但没有私人库标识时停止，请用户确认是否接入现有知识库。

初始化完成后运行：

```powershell
python scripts/private_library.py validate
python scripts/private_library.py show
```

两条命令都应从本机配置重新找到同一个根目录。重复初始化已经有效的同一个库时保留已有文件内容；Skill 新增的缺失模板会补齐，但不会覆盖用户已经修改的策略或模板。

## 接入现有库

用户可以直接说：

```text
使用 $100x-learning 接入现有私人知识库，位置是 E:\Knowledge\Existing Library。
```

用户明确指定一个已有知识库时运行：

```powershell
python scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
```

接入要求目标目录已有 `Home.md` 和完整的活动目录，只新增 100x-learning 的库标识并更新本机根目录配置，不移动、复制或改写现有知识内容。目录不符合当前私人库合同时，报告缺少的目录并停止。

## 正常任务怎样取得根目录

任何知识库读取或写入、内容案例维护、钩子维护、写作记忆检索开始前，先运行：

```powershell
python scripts/private_library.py show
```

把返回的 `library_root` 作为本次唯一的 `<私人知识库>`。后续所有路径都相对这个根目录解释。当前任务明确给出另一个库时，可以在相应脚本上使用 `--library-root <路径>`；这只覆盖本次调用，不改变已保存的默认库。

`show` 同时返回可选的 `marktree_cli`。用户要让 Marktree 与本 Skill 共管同一个私人库时，先构建或安装 Marktree CLI，再运行：

```powershell
python scripts/private_library.py configure-marktree --cli "D:\Tools\Marktree\marktree-cli.exe"
python scripts/marktree_integration.py status
```

状态结果中的 `data.root` 必须与 `library_root` 指向同一个实际目录。`data.git` 为空表示普通工作区；这种情况下 Marktree 仍会显示 Agent 的真实文件结果，但不会生成 Git 变更清单。只有私人库根目录自身存在 `.git` 时才进入 Marktree 的精确 Git 链路，禁止借用父目录仓库。

Marktree 只负责工作区范围、保留原文、避免同时写入冲突、操作恢复和可选 Git；本 Skill 继续决定知识、来源、项目、成果、案例和钩子分别该放在哪里。不要在 Marktree 内复制一套知识分类规则。

普通写作先使用版本控制内分开存放的组件模板目录。私人库已经配置且可读时，主流程可以运行 `scripts/select_writing_examples.py candidates` 查看本次钩子、正文、结尾和长文章节组件的候选标题，再通过 `render` 只读取模型按当前角度显式选择的完整模仿例子；不读取同主题知识、作者声音、发布历史或其它私人材料。没有相关候选、私人库配置不存在或路径不可达时省略模仿例子，仍按组件职责直接成文。

用户明确要求初始化、接入、检查、维护或写入私人知识库时，配置和目录状态才是当前结果的一部分。此时准确报告缺失内容并停止，不能假装已经写入；用户要求的结果必须保存到本机但没有可用位置时，只询问保存位置。

## 完成结果

初始化或接入成功后，第一段直接告诉用户私人库已经可用，再列出实际根目录、本机配置和验证结果。不要把库内部字段、目录创建日志或脚本输出原样当成交付。
