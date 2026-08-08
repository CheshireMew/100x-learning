from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class SkillStructureTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = _read("SKILL.md")
        routed = set(re.findall(r"`(references/[^`]+\.md)`", skill))
        active = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in (PROJECT_ROOT / "references").glob("*.md")
        }
        self.assertEqual(active, routed)
        self.assertTrue(all((PROJECT_ROOT / path).is_file() for path in routed))

    def test_references_do_not_select_sibling_references(self) -> None:
        paths = sorted((PROJECT_ROOT / "references").glob("*.md"))
        active_names = {path.name for path in paths}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            mentioned = sorted(
                name for name in active_names if name != path.name and name in text
            )
            self.assertEqual([], mentioned, path)

    def test_new_writing_uses_private_references_but_local_edits_do_not(self) -> None:
        skill = _read("SKILL.md")
        private_library = _read("references/private-knowledge-library.md")
        self.assertIn("材料完备短内容", skill)
        self.assertIn("发现式新写", skill)
        self.assertIn("scripts/private_library.py show", skill)
        self.assertIn("不联网补材料，但仍读取私人案例与钩子", skill)
        self.assertIn("本人现稿", skill)
        self.assertIn("等义压缩", skill)
        self.assertIn("没有配置私人库", private_library)

    def test_reference_retrieval_is_split_by_form_and_only_by_technique(self) -> None:
        skill = _read("SKILL.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        contract = "\n".join((skill, cases, hooks))

        for name in (
            "短内容案例索引.md",
            "文章案例索引.md",
            "短内容钩子索引.md",
            "Thread钩子索引.md",
            "文章钩子索引.md",
        ):
            self.assertIn(name, contract)
        self.assertIn("只按", contract)
        self.assertIn("写作技巧", contract)
        self.assertIn("对象名、平台名、行业名和主题词不能用于案例检索", cases)
        self.assertIn("对象名、平台名、行业名和主题词不能用于钩子检索", hooks)
        self.assertIn("不能跨形态", skill)

        for old_contract in (
            "/内容案例索引.md",
            "/开头钩子索引.md",
            "index_task",
            "index_topics",
            "index_moves",
            "promotion_stages",
            "benefit_recipients",
        ):
            self.assertNotIn(old_contract, contract)

    def test_references_are_complete_inputs_not_topic_templates(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        cases = _read("references/content-case-library.md")
        hooks = _read("references/hook-library.md")
        self.assertIn("完整案例和钩子原文能在当前上下文直接阅读", skill)
        self.assertIn("只有索引、标题、摘要或文件名不算完成交接", skill)
        self.assertIn("阅读全文", cases)
        self.assertIn("阅读全文", hooks)
        self.assertIn("few-shot 写作输入", skill)
        self.assertIn("读取原文后直接进入成文", skill)
        self.assertIn("固定打开三份技巧组合不同的完整短内容案例", skill)
        self.assertIn("两份开头技巧不同", skill)
        self.assertIn("案例和钩子是 few-shot", content)
        self.assertIn("不先归纳技巧、指定模板或证明用途", cases)
        self.assertIn("不复制表面句型", hooks)

    def test_model_has_freedom_inside_real_hard_boundaries(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        self.assertIn(
            "用户要求、事实、来源身份、目标语言、成品形式和明确长度是硬边界",
            skill,
        )
        self.assertIn("自行决定写什么、从哪里开始、怎样推进和在哪里停", content)
        self.assertIn("材料越多越需要取舍", content)
        self.assertIn("不必逐项覆盖", content)
        self.assertIn("不设字数上限或下限", content)
        self.assertIn("不能把字数当作完成度", content)
        self.assertNotIn("先看见最值得知道的变化，再用必要事实", skill)
        self.assertNotIn("只使用对象亮相、主要利益、参与动作和结果收束", skill)
        self.assertNotIn("临时删除最后一到两段", skill)

    def test_writer_receives_full_references_without_precomputed_copy_plan(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        contract = "\n".join((skill, content))
        self.assertIn("完整案例纯正文、完整钩子纯正文", skill)
        self.assertIn("最后连续阅读三份完整短内容案例", content)
        self.assertIn("不要先总结技巧", content)
        self.assertIn("案例标题、路径、机器字段", skill)
        self.assertIn("检索技巧名、选择理由、预写摘要、段落分工", skill)
        self.assertNotIn("任务合同", contract)
        self.assertNotIn("最该记住什么", contract)
        self.assertNotIn("最有直接后果", contract)

    def test_source_material_does_not_become_user_voice(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        self.assertIn("粘贴的文字默认都是参考材料", skill)
        self.assertIn("都属于来源作者", skill)
        self.assertIn("不借用案例中的人物、经历、立场、第一人称", content)
        self.assertIn("不能成为事实来源或用户长期声音", natural)
        self.assertIn("来源作者被写成用户", natural)

    def test_natural_review_judges_the_complete_draft_without_a_phrase_blacklist(self) -> None:
        skill = _read("SKILL.md")
        natural = _read("references/natural-writing.md")
        self.assertIn("初稿已经冻结后使用", natural)
        self.assertIn("逐句做一次删除测试", natural)
        self.assertIn("如果没有新增事实、关系、动作或必要情绪，一律删除", natural)
        self.assertIn("润色默认保留初稿，有明确问题才改", natural)
        self.assertIn("如果新写法没有更准确、更具体、更清楚或更顺，保留原句", natural)
        self.assertIn("润色不设字数上限或下限", natural)
        self.assertIn("从最后一句开始倒序做唯一贡献测试", natural)
        self.assertIn("只宣布“变化很大、规则变了、换玩法了、不是 A 而是 B”", natural)
        self.assertIn("首句应使用当前材料独有的事实、动作、冲突或结果", natural)
        self.assertIn("删完不再补结尾", skill)
        self.assertIn("不要套固定的“AI 味词表”", natural)
        self.assertIn("保留初稿里已经成立的具体感、节奏、留白和人的毛边", natural)
        self.assertIn("同时展示修改前与修改后", natural)

    def test_finished_language_is_separate_from_source_language(self) -> None:
        skill = _read("SKILL.md")
        content = _read("references/content-writing.md")
        natural = _read("references/natural-writing.md")
        self.assertIn("成品语言与来源语言分开处理", skill)
        self.assertIn("目标语言已有清楚说法时直接使用", content)
        self.assertIn("目标语言受外文牵制", natural)
        self.assertIn("需要识别、搜索或操作原名", content)

    def test_every_writing_delivery_shows_actual_references_and_sources(self) -> None:
        skill = _read("SKILL.md")
        self.assertIn("**写作要求**", skill)
        self.assertIn("只写一句话", skill)
        self.assertIn("材料事实、必写重点、来源身份、处理路线", skill)
        self.assertIn("**修改前**", skill)
        self.assertIn("**修改后**", skill)
        self.assertIn("润色不是为了产生差异", skill)
        self.assertIn("修改后没有更好时", skill)
        self.assertNotIn("**写作使用的材料**", skill)
        self.assertIn("本次创作参考", skill)
        self.assertIn("本次信息来源", skill)


if __name__ == "__main__":
    unittest.main()
