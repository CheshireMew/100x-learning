# 参与 100x Learning

感谢你愿意改进 100x Learning。这个仓库交付三个 Agent Skills：`skills/100x-learning`、`skills/private-knowledge` 和 `skills/content-system`。每个 `SKILL.md` 只负责自己的用户结果，目录内的 `references/` 保存方法，`scripts/` 负责确定性操作，根级 `tests/` 保护跨 Skill 的生产消费链和资源边界。

## 开始前

先查看 [skills/](./skills/) 中与你的改动对应的 `SKILL.md`、reference、脚本与测试。缺陷修复应沿着真实入口找到唯一真源，一次迁移生产者和消费者；已经退休的路径放在 `archive/`，不能重新接回活动路由。

如果你准备新增能力，请先确认它产生的是新的用户结果，还是现有结果中的方法细节。新的独立结果才考虑新增 Skill；现有结果的完整方法由对应入口的一份明确 reference 负责，不要把同一规则同时复制到 README、多个 reference 和脚本里。

## 提交改动

1. 让改动保持在一个清楚的结果范围内，并保留仓库中无关的现有变化。
2. 为行为变化补充直接覆盖生产与消费链的测试。不要由消费端手写假索引、假状态或假产物来代替正式生产者。
3. 只在公开身份、首次使用路径、能力边界、许可证或维护入口变化时更新 README；内部方法细节保留在唯一真源中。
4. 新增或修改脚本时优先使用 Python 标准库，并保持 Windows、macOS 与 Linux 能读取仓库内的相对路径。
5. 不要提交私人知识库、生成输出、缓存或本机配置；这些路径由 [.gitignore](./.gitignore) 排除。

运行完整行为测试：

```bash
python -m pytest -q
```

只修改文档时，不需要运行与改动无关的端到端测试，但必须检查 Markdown 链接、命令、图片和所陈述的项目事实。

## Pull Request

Pull Request 请说明读者或用户会看到什么变化、活动真源位于哪里、旧路径怎样退出，以及你运行了哪些检查。若改动涉及第三方代码、模板、文章、图片、数据或其它资源，请同时写明原始来源、许可证、修改方式和目标路径。

提交贡献前，请确认你有权提供相关内容，并允许它按本仓库的 [LICENSE](./LICENSE) 与 [LICENSING.md](./LICENSING.md) 所述范围分发。第三方材料继续遵守其自身条款。
