from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class WritingContractTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = _read("SKILL.md")
        routed = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }

        self.assertEqual(active, routed)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in routed))

    def test_references_do_not_route_other_references(self) -> None:
        for path in (PROJECT_ROOT / "references").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"读取 `references/[^`]+\.md`", path)

    def test_output_identity_is_selected_before_publication_facts(self) -> None:
        skill = _read("SKILL.md")
        identity = skill.index("### 2. 选择写作动作和成品身份")
        publication = skill.index("### 3. 按需叠加发布事实")
        self.assertLess(identity, publication)
        self.assertIn("单个 GitHub 项目介绍", skill)
        self.assertIn("普通写作流程完成", skill)

    def test_material_preparation_preserves_source_relationships(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")

        self.assertIn("事实、上下文、行动者、动作、先后关系、原因、结果", prewrite)
        self.assertIn("不解释专业词和内部说法", prewrite)
        self.assertIn("材料准备阶段不为目标读者补解释", prewrite)
        self.assertIn("不要只留下对整段材料的概括", prewrite)
        self.assertIn("不要把原文改造成另一套“麻烦、动作、变化”等摘要", prewrite)
        self.assertIn("来源原始措辞、必要术语、完整事实关系", content)
        self.assertIn("通俗易懂和传播力都在写正文时完成", content)
        self.assertLess(
            skill.index("### 2. 发现并准备有现实感的写作材料"),
            skill.index("### 5. 形成一篇首尾完整的内容"),
        )

    def test_external_search_expands_material_for_new_writing(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")

        self.assertIn("读取用户材料、对象真源和外部来源", skill)
        self.assertIn("并通过网络搜索扩充创作材料", prewrite)
        self.assertIn("新来源不再增加场景、细节、比较或说法时停止", prewrite)

    def test_short_writing_does_not_load_article_cases(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")

        self.assertIn("普通短帖、产品帖和 GitHub 项目短介绍只从完整短内容中找案例", skill)
        self.assertIn("文章与 Newsletter 才读取文章案例", skill)
        self.assertIn("短内容只查完整短内容", cases)
        self.assertIn("网络搜索得到的新闻、评测、博客和其它文章是当前对象的外部材料", cases)
        self.assertIn("不因此成为文章案例", cases)

    def test_author_voice_remains_conditional(self) -> None:
        skill = _read("SKILL.md")

        self.assertIn("### 3. 按需取得作者声音", skill)
        self.assertIn("只有用户要求延续本人写法", skill)
        self.assertIn("不自动加载文章案例或作者声音", skill)

    def test_references_are_direct_creative_inputs_without_status_workflow(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        active_writing = "\n".join((skill, cases, hooks, content, natural))

        self.assertIn("实际打开的完整案例与钩子直接参与当前写作", skill)
        self.assertIn("模型直接从全文感受信息选择", cases)
        self.assertIn("让模型自由综合", hooks)
        self.assertIn("模型阅读全文后自由综合", content)
        for retired in (
            "候选参考",
            "生产参考",
            "生产输入",
            "临时生产包",
            "明确切换到成文阶段",
            "不另调子 Agent",
            "API 或 CLI",
            "开始成文前的交接",
        ):
            self.assertNotIn(retired, active_writing)

    def test_cases_and_hooks_keep_separate_management_but_share_writing(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")

        self.assertIn("案例与钩子独立生产，共同参与写作", skill)
        self.assertIn("它不管理钩子", cases)
        self.assertIn("它不读取完整案例", hooks)
        self.assertIn("多份钩子和多份完整案例", hooks)
        self.assertIn("先按开头手法、再按原始成品形态", hooks)

    def test_short_writing_has_one_center_and_a_complete_arc(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        project = _read("references/github-project-short-content.md")

        self.assertIn("读者读完只需要记住哪一件事", skill)
        self.assertIn("开头把它自然带出来、正文把它讲清楚、结尾把它说完", skill)
        self.assertIn("先确定整篇要说完的一件事", content)
        self.assertIn("开头把读者自然带进来", content)
        self.assertIn("结尾是否完成前文", natural)
        self.assertIn("先确定这次介绍最值得读者记住的一件事", project)

    def test_review_reads_the_whole_draft_before_fact_and_language_checks(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")

        self.assertLess(
            skill.index("### 5. 形成一篇首尾完整的内容"),
            skill.index("### 6. 回读内容与表达"),
        )
        self.assertLess(
            natural.index("## 先读整篇是否成立"),
            natural.index("## 再核对草稿实际写出的内容"),
        )
        self.assertLess(
            natural.index("## 再核对草稿实际写出的内容"),
            natural.index("## 检查读者能否顺畅理解"),
        )
        self.assertIn("重新选择中心并组织整篇", natural)

    def test_continuous_feedback_becomes_a_positive_result_not_a_blacklist(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")

        self.assertIn("全文怎样完整说完一件事", skill)
        self.assertIn("任务合同只保留这些最终要求", skill)
        self.assertIn("任务合同只描述这次成品应当呈现的正面结果", content)
        self.assertNotIn("像 AI、套产品文案", skill)
        self.assertNotIn("痛点—对象亮相—能力罗列—行动入口", skill)
        self.assertNotIn("制造痛点—解释痛点", content)

    def test_user_selected_content_priority_reaches_each_consumer(self) -> None:
        skill = _read("SKILL.md")
        prewrite = _read("references/prewriting-research.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("只要求提到、带到、顺带说明或不要漏掉", skill)
        self.assertIn("只要求提到或带到的信息只作为配角材料", prewrite)
        self.assertIn("不单独决定开头、主要篇幅和展开深度", content)
        self.assertIn("应当服务中心", natural)

    def test_unfamiliar_subject_is_identified_in_plain_language(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")

        for text in (skill, content, natural):
            self.assertIn("第一次遇到", text)
            self.assertIn("人、事、概念、产品或组织", text)
            self.assertIn("它是什么或是谁", text)
            self.assertIn("和眼前内容有什么关系", text)
        self.assertIn("界面动作和名称直接使用", content)

    def test_github_project_identity_is_complete_without_feature_dumping(self) -> None:
        project = _read("references/github-project-short-content.md")

        self.assertIn("项目的总定位与完整能力范围", project)
        self.assertIn("正文不需要逐项罗列全部能力", project)
        self.assertIn("不能用它们重新定义整个项目", project)
        self.assertIn("结尾完成这次介绍", project)

    def test_writing_delivery_keeps_three_code_blocks_and_actual_references(self) -> None:
        skill = _read("SKILL.md")

        self.assertIn("任务合同", skill)
        self.assertIn("传给写作 AI 的内容", skill)
        self.assertIn("写作 AI 的成品内容", skill)
        self.assertIn("分别放在独立代码块中", skill)
        self.assertIn("正文自身含代码围栏时使用更长的外层围栏", skill)
        self.assertIn("本次创作参考", skill)
        self.assertIn("本次实际使用了创作参考时", skill)
        self.assertIn("使用可点击的绝对文件路径", skill)

    def test_writer_does_not_receive_conservative_or_anti_fabrication_prompts(self) -> None:
        content = _read("references/content-writing.md")
        for text in (
            "不得虚构",
            "公开仓库目前没有可用的 Issue",
            "材料缺口",
            "保守判断",
            "风险备注",
            "成稿检查表",
        ):
            self.assertNotIn(text, content)

    def test_action_entry_follows_the_reader_next_step(self) -> None:
        content = _read("references/content-writing.md")
        publication = _read("references/publication-requirements.md")
        natural = _read("references/natural-writing.md")

        self.assertIn("正文已经建立的读者下一步", content)
        self.assertIn("一个最有用的主要入口", content)
        self.assertIn("无法完成正文承诺", natural)
        self.assertIn("行动入口由正文已经建立的读者下一步决定", publication)

    def test_material_based_writing_remains_creative(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        prewrite = _read("references/prewriting-research.md")

        self.assertIn("不把它解释成忠实摘要合同", skill)
        self.assertIn("材料提供内容，不要求沿用原材料的措辞和顺序", content)
        self.assertIn("角度、主线、开头、结构和结尾由写作时决定", prewrite)

    def test_language_defaults_to_chinese_once(self) -> None:
        self.assertIn("没有指定时，直接回复和可发布文字默认使用中文", _read("SKILL.md"))

    def test_voice_and_novelty_remain_separate(self) -> None:
        skill = _read("SKILL.md")
        memory = _read("references/personal-writing-memory.md")

        self.assertIn("内容查重只在用户要求查重", skill)
        self.assertIn("voice", skill)
        self.assertIn("novelty", skill)
        self.assertIn("两条检索结果不能互相代用", memory)


if __name__ == "__main__":
    unittest.main()
