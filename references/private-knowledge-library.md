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

没有给保存位置时只询问这一项。新库必须位于 Skill 目录之外。初始化器会建立 `Home.md`、知识、来源、案例、钩子、成果、写作系统和归档目录，并把唯一根目录记录到当前用户的 `~/.100x-learning/config.json`。目标目录已经包含其它内容但没有私人库标识时停止，请用户确认是否接入现有知识库。

初始化完成后运行：

```powershell
python scripts/private_library.py validate
python scripts/private_library.py show
```

两条命令都应从本机配置重新找到同一个根目录。重复初始化已经有效的同一个库时保持现有文件不变，只报告它已经就绪。

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

配置不存在、根目录不可达或库版本无效时，把这个状态直接交回上层。普通理解、研究和写作继续使用当前材料；用户要求的结果必须持久化时，询问初始化或接入位置后停止。

## 完成结果

初始化或接入成功后，第一段直接告诉用户私人库已经可用，再列出实际根目录、本机配置和验证结果。不要把库内部字段、目录创建日志或脚本输出原样当成交付。
