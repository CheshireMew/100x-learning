from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class SkillStructureTests(unittest.TestCase):
    def test_skill_references_every_active_reference(self) -> None:
        skill = _read("SKILL.md")
        referenced = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").rglob("*.md")
        }
        self.assertEqual(active, referenced)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in referenced))

    def test_references_do_not_route_to_sibling_references(self) -> None:
        paths = sorted((PROJECT_ROOT / "references").glob("*.md"))
        active_names = {path.name for path in paths}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            mentioned = sorted(
                name for name in active_names if name != path.name and name in text
            )
            allowed = {
                "content-case-library.md": {"writing-template-coverage.md"},
                "hook-library.md": {"writing-template-coverage.md"},
                "writing-template-maintenance.md": {"writing-template-coverage.md"},
            }.get(path.name, set())
            self.assertEqual([], [name for name in mentioned if name not in allowed], path)

    def test_normal_writing_selects_independent_components(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        index = _read("references/writing-templates/index.md")
        contract = "\n".join((skill, content, index))

        self.assertIn("分开选择每个写作部件", skill)
        self.assertIn("分别选择一个钩子、承接、正文推进、连接和结尾", index)
        self.assertIn("组件可以独立组合，不预先绑定成整篇路线", skill)
        self.assertIn("组件独立选择，不使用整篇模板、固定套餐或推荐组合", content)
        for field in ("钩子：<Hxx", "承接：<Cxx", "正文：<Pxx", "连接：<Bxx", "章节：<文章", "结尾：<Exx"):
            self.assertIn(field, content)
        self.assertIn("【模仿例子】", content)
        self.assertIn("组件文件不提供可以填空的成品句", content)
        self.assertIn("模板管职责，真实例子帮助表达", skill)
        self.assertNotIn("逐组件槽位绑定", content)
        self.assertNotIn("模板给句法，材料填槽位", skill)
        self.assertNotIn("writing-template-catalog.md", contract)

    def test_old_case_and_hook_mixing_runtime_is_gone(self) -> None:
        runtime_paths = ["SKILL.md"] + [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in sorted((PROJECT_ROOT / "references").rglob("*.md"))
        ]
        runtime = "\n".join(_read(path) for path in runtime_paths)
        for retired in (
            "【参考案例】",
            "【参考开头】",
            "默认选入三份",
            "三个不同的写作技巧分组",
            "沿索引打开的完整案例",
            "沿索引打开的完整钩子",
            "临时参考不自动保存",
            "重新选择案例与钩子",
            "完整案例和开头钩子实际参与表达",
            "选入的每份案例和钩子都应当真实参与写作",
            "每次写作在同一次回复中固定展示四部分",
            "本次创作参考",
            "每篇只选择一个完整模板",
            "禁止跨模板拼装",
            "短帖或 Thread 只能选择 `T` 模板",
            "文章或 Newsletter 只能选择 `A` 模板",
        ):
            self.assertNotIn(retired, runtime)

        skill = _read("SKILL.md")
        self.assertIn("普通写作只从私人库读取当前组件需要的模仿例子", skill)
        self.assertIn("为本次选中的 `H`、`P`、`E` 分别取得一份完整真实例子", skill)
        self.assertIn("不读取同主题知识、作者声音、发布历史或其它私人材料", _read("references/private-knowledge-library.md"))

    def test_writer_input_has_material_components_and_optional_voice(self) -> None:
        content = _read("references/content-writing.md")
        for heading in ("【用户要求】", "【材料】", "【结构组件】", "【模仿例子】", "【作者声音】"):
            self.assertEqual(1, content.count(heading), heading)
        for retired in ("【参考案例】", "【参考开头】", "【完整案例】", "【完整钩子】"):
            self.assertNotIn(retired, content)
        self.assertIn("专项说明、维护规则、检索过程、覆盖账本和与当前对象无关的旧稿不进入", content)
        self.assertIn("模仿例子单独标明职责，不与本轮事实混放", content)
        self.assertIn("必须事实”只用于判断当前材料是否足以使用这个组件，不转成填空字段", content)
        self.assertIn("模仿例子可以影响句子长短、信息密度、推进速度和停笔方式", content)
        self.assertIn("人物、对象、数字、观点、情绪和行动入口不能进入本轮成品", content)
        self.assertNotIn("只把绑定好的事实片段填入槽位", content)

    def test_every_component_has_its_own_file_and_schema(self) -> None:
        root = PROJECT_ROOT / "references" / "writing-templates"
        expected = {
            "hooks": ("H", 23),
            "continuations": ("C", 12),
            "bodies": ("P", 24),
            "bridges": ("B", 16),
            "endings": ("E", 18),
            "sections": ("S", 9),
        }
        seen: set[str] = set()
        for directory, (prefix, count) in expected.items():
            paths = sorted((root / directory).glob("*.md"))
            self.assertEqual([f"{prefix}{i:02d}.md" for i in range(1, count + 1)], [p.name for p in paths])
            for path in paths:
                component_id = path.stem
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, rf"^# {component_id} .+", path)
                self.assertIn("- 适用条件：", text, path)
                self.assertIn("- 必须事实：", text, path)
                for rigid_field in ("- 固定骨架：", "- 固定写法：", "- 固定顺序：", "- 句面骨架：", "- 条件句骨架：", "- 结构示例：", "第二句骨架", "每点骨架", "每组骨架"):
                    self.assertNotIn(rigid_field, text, path)
                self.assertNotIn("[", text, path)
                self.assertNotIn("- 禁用：", text, path)
                self.assertNotIn(component_id, seen)
                seen.add(component_id)

    def test_coverage_ledger_accounts_for_every_active_source_once(self) -> None:
        coverage = _read("references/writing-template-coverage.md")
        case_ids = re.findall(r"^\| `(case-[^`]+)` \|", coverage, flags=re.MULTILINE)
        hook_ids = re.findall(r"^\| `((?:short|thread)-hook-[^`]+)` \|", coverage, flags=re.MULTILINE)
        self.assertEqual(70, len(case_ids))
        self.assertEqual(70, len(set(case_ids)))
        self.assertEqual(131, len(hook_ids))
        self.assertEqual(131, len(set(hook_ids)))
        self.assertEqual(8, coverage.count("降权：与活动案例开头语义重复"))
        self.assertIn("指向它实际支持的组件或明确拒绝原因", coverage)
        component_files = {
            path.stem
            for path in (PROJECT_ROOT / "references" / "writing-templates").rglob("*.md")
            if path.name != "index.md"
        }
        covered_components = set(re.findall(r"`([HCPBES]\d{2})`", coverage))
        self.assertEqual(component_files, covered_components)

    def test_template_selection_rejects_missing_facts(self) -> None:
        index = _read("references/writing-templates/index.md")
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((index, skill, content))
        self.assertIn("每个组件只看自己的“适用条件”和“必须事实”", index)
        self.assertIn("缺少事实就换同类组件", index)
        self.assertIn("不能让模仿例子补充本轮人物、事实、观点、情绪或行动入口", skill)
        self.assertIn("必须事实”只用于判断当前材料是否足以使用这个组件", content)
        self.assertIn("第一人称、亲历、测试、时间、数字、引语、因果、比较和最高级", contract)
        self.assertIn("不能提供本轮人物、痛点、情绪、体验、意义、读者心理或行动入口", contract)
        self.assertIn("任何必需类别都没有合格组件时不成文", skill)

    def test_user_can_replace_only_the_component_they_specified(self) -> None:
        index = _read("references/writing-templates/index.md")
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((index, skill, content))
        for component in ("USER-H", "USER-C", "USER-P", "USER-B", "USER-E", "USER-S"):
            self.assertIn(component, contract)
        self.assertIn("只把这一部分记为", index)
        self.assertIn("用户没有规定的内容不能从局部要求中推断", index)
        self.assertIn("用户结构要求", content)
        self.assertNotIn("把用户结构视为本次唯一模板", contract)

    def test_sources_and_current_drafts_are_not_mistaken_for_style_examples(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, content))
        self.assertIn("本次任务的事实来源、用户明确交付的待改正文和来源消化对象仍作为材料使用", content)
        self.assertIn("用户明确交付的待改正文和来源消化对象仍作为材料使用", content)
        self.assertIn("与当前对象无关的旧稿不进入", content)

    def test_workflow_components_are_independent(self) -> None:
        hook = _read("references/writing-templates/hooks/H23.md")
        continuation = _read("references/writing-templates/continuations/C02.md")
        body = _read("references/writing-templates/bodies/P01.md")
        ending = _read("references/writing-templates/endings/E04.md")
        self.assertIn("原始输入或动作", hook)
        self.assertIn("成品本身是操作演示、教程或命令讲解", hook)
        self.assertIn("成品本身是操作演示、教程、命令讲解或具体工作流说明", body)
        self.assertIn("可见输出或结果", continuation)
        self.assertIn("输入（前文已经写出时不复述）→ 输出 → 中间动作 → 能力证据", body)
        self.assertIn("单一来源或入口", ending)

    def test_project_promotion_hook_intent_does_not_bind_other_components(self) -> None:
        index = _read("references/writing-templates/index.md")
        project = _read("references/github-project-short-content.md")
        content = _read("references/content-writing.md")
        evidence_body = _read("references/writing-templates/bodies/P24.md")
        contract = "\n".join((index, project, content))
        self.assertIn("项目介绍或宣传短帖优先用 `H01` 的具体利益、`H02` 的可见结果", index)
        self.assertIn("`H23` 留给操作演示、教程和命令讲解", index)
        self.assertIn("`P01` 留给操作演示、教程、命令讲解和具体工作流说明", index)
        self.assertIn("正文可以用 `P24 结果证据展开`", project)
        self.assertIn("钩子、承接、正文、连接和结尾仍分别按自身条件判断", content)
        self.assertIn("二至四项彼此不同的能力、数量、格式或范围", evidence_body)
        self.assertIn("不复述前文已经写出的结果、利益、命令或输出", evidence_body)
        self.assertIn("同一谓语下的两项同类事实合成一句", evidence_body)

    def test_surface_templates_use_direct_chinese(self) -> None:
        root = PROJECT_ROOT / "references" / "writing-templates"
        runtime = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.md"))
        for translated in (
            "做这件事的是[对象名]",
            "让这件事看起来不可能",
            "反证]指向的是",
            "很多人还不知道",
            "最终得到的是",
            "最直接的证据是",
            "开头的[对象]",
            "目前只能确定",
            "这个答案不成立",
            "超出这个范围，不能推出",
            "我实际会用的是这",
            "让[结果]成为可能",
            "目前还不能确认",
            "下面是它真正展开的",
            "不过，这只在[条件]下成立",
            "和实际的[状态 B]对不上",
            "[B/约束]不允许",
        ):
            self.assertNotIn(translated, runtime)
        self.assertIn("定位、机制和结果各自落清楚", _read("references/writing-templates/bodies/P04.md"))
        self.assertIn("案例必须先完整结束", _read("references/writing-templates/bodies/P18.md"))
        problem_body = _read("references/writing-templates/bodies/P05.md")
        for fact in ("问题主体", "触发动作或状态", "可观察异常"):
            self.assertIn(fact, problem_body)
        self.assertIn("主张 → 定义 → 机制 → 证据", _read("references/writing-templates/bodies/P13.md"))
        self.assertNotIn("我更关注", _read("references/writing-templates/continuations/C07.md"))
        self.assertIn("只有研究规模本身是主题时才用样本量", _read("references/writing-templates/hooks/H16.md"))
        for ai_turn in ("真正的", "真正决定", "本质上", "不是要不要", "更像", "表面上"):
            self.assertNotIn(ai_turn, runtime)
        self.assertNotIn("[", runtime)

    def test_generic_templates_do_not_require_caveats(self) -> None:
        root = PROJECT_ROOT / "references" / "writing-templates"
        generic_ids = (
            "C03", "P03", "P04", "P05", "P06", "P07", "P08", "P09",
            "P11", "P13", "P18", "P20", "P23", "P24",
            "S02", "S04", "S07", "S08", "E14",
        )
        for component_id in generic_ids:
            path = next(root.rglob(f"{component_id}.md"))
            required = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- 必须事实："))
            for caveat in ("限制", "边界", "未知", "反方", "例外", "失效条件"):
                self.assertNotIn(caveat, required, component_id)

    def test_long_writing_constrains_each_section(self) -> None:
        index = _read("references/writing-templates/index.md")
        content = _read("references/content-writing.md")
        article = _read("references/article-from-practice.md")
        contract = "\n".join((index, content, article))
        self.assertIn("长文可以让不同章节各选一个 `S`", index)
        self.assertIn("文章与 Newsletter 的每个章节还必须出现一个 `S`", content)
        self.assertIn("全文推进从一个 `P` 取得", article)
        self.assertIn("不能把多个正文推进模板当成多个章节拼接", article)
        self.assertIn("CTA 由结尾 `E` 决定", article)
        self.assertIn("最多一个", article)

    def test_case_and_hook_libraries_are_research_corpus_and_scoped_examples(self) -> None:
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        maintenance = _read("references/writing-template-maintenance.md")
        home = _read("assets/private-library/Home.md")
        self.assertIn("独立组件模板的蒸馏语料", cases)
        self.assertIn("正式取例工具选为钩子、正文、结尾或长文章节的完整模仿例子", cases)
        self.assertIn("独立钩子与承接组件的蒸馏语料", hooks)
        self.assertIn("正式取例工具为当前钩子组件返回的一份完整例子", hooks)
        self.assertIn("普通写作不读取本文件", maintenance)
        self.assertIn("钩子、承接、正文推进、连接、结尾和长文章节必须分开蒸馏、分开存放", maintenance)
        self.assertIn("不建立推荐套餐或兼容矩阵", maintenance)
        self.assertIn("分开存放的钩子、承接、正文、连接、结尾和章节组件模板", home)

    def test_material_preparation_preserves_source_boundaries(self) -> None:
        preparation = _read("references/writing-material-preparation.md")
        promotion = _read("references/project-promotion-materials.md")
        self.assertIn("准备后的材料是成文输入，不是正文提纲", preparation)
        self.assertIn("事实、关系、判断、猜测、问题、宣发角度和内容主次作为材料保留原话", preparation)
        self.assertIn("来源身份和原有确定程度", preparation)
        self.assertIn("不摘要、转述、重排、拼接或统一改写", preparation)
        self.assertIn("当前仍成立的开放问题和候选机制继续保留", promotion)
        self.assertIn("项目方发给作者邀请码", promotion)
        self.assertIn("正文按选中组件的职责和推进关系取舍", promotion)

    def test_writing_completes_in_one_turn_without_handoff(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, preparation, content))
        self.assertIn("材料准备、选模、取例和成文在同一次回复中连续完成", skill)
        self.assertIn("材料准备与联网补充只执行一次", preparation)
        self.assertNotIn("writing-handoff.md", contract)
        self.assertNotIn("正式交接文件", contract)
        self.assertNotIn("第一轮：交出正式准备文件", contract)

    def test_writing_browses_for_supplement_without_prewrite_fact_check(self) -> None:
        skill = _read("SKILL.md")
        preparation = _read("references/writing-material-preparation.md")
        contract = "\n".join((skill, preparation))
        self.assertIn("写作前可以联网发现", contract)
        self.assertIn("用户明确要求联网补充时直接执行", contract)
        self.assertIn("明确禁止联网", contract)
        self.assertIn("只使用给定材料", contract)
        self.assertIn("只改错字、格式和等义措辞", contract)
        self.assertIn("联网补充不是研究或事实核查", skill)
        self.assertIn("不是逐项验证用户已经给出的说法", preparation)
        self.assertIn("不生成事实核查报告", preparation)
        self.assertIn("不以核查完成作为开始写作的前置条件", skill)
        self.assertIn("新增内容保持来源身份和原有确定程度", preparation)

    def test_plan_mode_supplements_before_interviewing(self) -> None:
        skill = _read("SKILL.md")
        plan = skill.split("### Plan 模式下先补充再访谈", 1)[1].split(
            "### 默认模式下准备并直接成文", 1
        )[0]
        self.assertIn("用户主动开启 Plan 模式视为明确的深度访谈请求", plan)
        self.assertIn("必须先完成本次需要的联网补充", plan)
        self.assertIn("再使用 `request_user_input` 开始访谈", plan)
        self.assertLess(
            plan.index("必须先完成本次需要的联网补充"),
            plan.index("再使用 `request_user_input` 开始访谈"),
        )
        self.assertIn("每轮只集中推进一个问题", plan)
        self.assertIn("不按固定问卷机械遍历", plan)

    def test_explicit_rewrite_reuses_facts_and_reselects_components(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("“重新写”“重写”“从头写”或等义表达", skill)
        self.assertIn("沿用已经确认的当前对象材料、表达边界和仍然适用的硬要求", skill)
        self.assertIn("不把上一稿及其句子、结构或纠错过程放入成文输入", skill)
        self.assertIn("重新独立选择各类合格组件，从零成文", skill)
        self.assertIn("只要求改字词、格式或等义措辞", skill)

    def test_default_delivery_returns_result_and_used_template_ids(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        index = _read("references/writing-templates/index.md")
        self.assertIn("默认先交付可直接使用的完整成品", skill)
        self.assertIn("随后固定列出本次使用的模板", skill)
        self.assertIn("默认不展示内部材料、组件选择过程、模仿例子、检查过程", skill)
        self.assertIn("把完整成品和“使用模板”清单一起交回主流程", content)
        for label in ("钩子：Hxx", "承接：Cxx", "正文：Pxx", "连接：Bxx", "章节：Sxx", "结尾：Exx"):
            self.assertIn(label, index)
        self.assertNotIn("**写作准备材料**", skill)
        self.assertNotIn("**本次创作参考**", skill)

    def test_author_voice_and_fact_checks_remain_opt_in_and_grounded(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")
        content = _read("references/content-writing.md")
        self.assertIn("普通写作只从私人库读取当前组件需要的模仿例子，不读取作者声音、发布历史或同主题知识", skill)
        self.assertIn("用户明确要求读取私人库中的既有声音", memory)
        self.assertIn("用户给出的文字默认是来源材料，不是用户本人写的现稿", content)
        self.assertIn("第一人称经历、使用体验", skill)
        self.assertIn("第一人称、亲历、测试、时间、数字、引语、因果、比较和最高级", content)

    def test_ai_flavor_audit_edits_only_confirmed_problems(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        audit = _read("references/content-audit.md")
        self.assertEqual(1, skill.count("references/natural-writing.md"))
        self.assertIn("用户要求检查或清理 AI 味时", skill)
        self.assertIn("没有内容作用的句子可以删除", natural)
        self.assertIn("删除后不补抽象总结", natural)
        self.assertIn("只修改已经确认的问题", audit)
        self.assertIn("不借审查重新设计全文", audit)

    def test_reference_admission_and_indexes_remain_maintainable(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("信息量与篇幅相称", cases)
        self.assertIn("可回查归档并重建索引", cases)
        self.assertIn("自然接入后文", hooks)
        self.assertIn("可回查归档并重建索引", hooks)
        self.assertIn("短帖和 Thread 都使用 `social`", skill)
        self.assertIn("独立短帖和 Thread 不再区分", cases)
        self.assertIn("不保存适用形式字段", hooks)
        for retired in ("短内容钩子索引.md", "Thread钩子索引.md", "文章钩子索引.md"):
            self.assertNotIn(retired, "\n".join((skill, cases, hooks)))

    def test_readmes_describe_template_runtime(self) -> None:
        readme = _read("README.md")
        readme_en = _read("README.en.md")
        readme_ja = _read("README.ja.md")
        self.assertIn("分开存放的钩子、承接、正文、连接、结尾和长文章节模板中独立选择", readme)
        self.assertIn("取例工具会为钩子、正文、结尾和实际使用的长文章节各挑一份完整案例", readme)
        self.assertNotIn("不读取私人案例、钩子", readme)
        self.assertIn("independently selects version-controlled hook, continuation, body, bridge, ending", readme_en)
        self.assertIn("example selector supplies one complete case for the hook, body, ending", readme_en)
        self.assertNotIn("does not read private cases, hooks", readme_en)
        self.assertIn("フック、承接、本文、接続、結び、長文セクションのテンプレートを個別に選び", readme_ja)
        self.assertIn("取例ツールはフック、本文、結び", readme_ja)
        self.assertNotIn("個人ライブラリの事例、書き出し、テーマ知識、個人の文体、公開履歴は読みません", readme_ja)

    def test_source_and_finished_languages_are_separate(self) -> None:
        self.assertIn("直接回复和可发布文字默认使用中文", _read("SKILL.md"))


if __name__ == "__main__":
    unittest.main()
