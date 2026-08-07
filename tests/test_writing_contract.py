from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_skill_routes_every_active_reference_to_an_existing_file(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
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

    def test_reference_materials_do_not_become_the_default_draft(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        prewriting = (PROJECT_ROOT / "references" / "prewriting-research.md").read_text(
            encoding="utf-8"
        )
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        natural_writing = (PROJECT_ROOT / "references" / "natural-writing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("写作使用的任务与材料", skill)
        self.assertIn("除非用户明确说明这是本人写的现稿", skill)
        self.assertIn("粘贴的文字默认都是参考材料", skill)
        self.assertIn("只是在重复或确认用户已经提供的", prewriting)
        self.assertIn("材料发现还没有完成", prewriting)
        self.assertIn("参考材料不是待修改正文", content_writing)
        self.assertIn("同一内容中心、同一信息顺序和同一段落作用", natural_writing)
        self.assertNotIn("材料净化只做删除", prewriting)
        self.assertIn("这些改写只发生在成品中", content_writing)
        self.assertNotIn("传给写作 AI", skill)
        self.assertNotIn("写作 AI 的成品内容", skill)

    def test_new_writing_requires_a_valid_private_reference_chain(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        writing_flow = skill.split("## 写作流程", maxsplit=1)[1]
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        private_library = (
            PROJECT_ROOT / "references" / "private-knowledge-library.md"
        ).read_text(encoding="utf-8")

        self.assertIn("普通新写、扩写和实质重组", skill)
        self.assertIn("scripts/private_library.py show", skill)
        self.assertIn("没有配置私人库", skill)
        self.assertIn("不能退回“只靠当前材料继续写”", skill)
        self.assertIn("在任何联网与外部材料发现之前", writing_flow)
        self.assertIn("这个失败分支不执行外部材料检索", writing_flow)
        self.assertLess(
            writing_flow.index("scripts/private_library.py show"),
            writing_flow.index("读取 `references/prewriting-research.md`"),
        )
        self.assertIn("不能自行改成无参考写作", content_writing)
        self.assertIn(
            "普通新写、扩写和实质重组在任何联网与外部材料发现之前立即停止",
            private_library,
        )

    def test_missing_private_references_cannot_fall_back_to_drafting(self) -> None:
        paths = [
            PROJECT_ROOT / "SKILL.md",
            PROJECT_ROOT / "references" / "content-writing.md",
            PROJECT_ROOT / "references" / "content-case-library.md",
            PROJECT_ROOT / "references" / "hook-library.md",
            PROJECT_ROOT / "references" / "private-knowledge-library.md",
            PROJECT_ROOT / "scripts" / "content_case_library.py",
        ]
        active_contract = "\n".join(
            path.read_text(encoding="utf-8") for path in paths
        )
        bypasses = (
            "私人库已经配置时，再读取",
            "私人库尚未初始化、参考库为空或没有合适参考时，使用当前材料和作者判断继续",
            "没有使用参考时不生成这个部分",
            "没有合适案例或钩子时，直接根据现有内容写作",
            "没有合适钩子时沿当前材料继续写",
            "找不到更贴合的案例时，可以根据现有事实和作者判断继续写",
        )

        for bypass in bypasses:
            self.assertNotIn(bypass, active_contract)
        self.assertIn("立即停止", active_contract)
        self.assertIn("停止成文", active_contract)

    def test_local_edit_is_the_only_reference_free_writing_route(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        private_library = (
            PROJECT_ROOT / "references" / "private-knowledge-library.md"
        ).read_text(encoding="utf-8")

        for text in (skill, content_writing, private_library):
            self.assertIn("本人现稿", text)
            self.assertIn("字词、格式或等义压缩", text)
        self.assertIn("真正互斥的执行路线", skill)
        self.assertIn("不改变原稿的观点和结构", skill)

    def test_reference_handoff_contains_full_text_and_affects_drafting(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("完整案例和钩子原文都能在当前上下文直接阅读", skill)
        self.assertIn("只有索引、标题、摘要或文件名不算完成交接", skill)
        self.assertIn("让案例实际影响信息怎样推进", skill)
        self.assertIn("让钩子实际影响开头怎样接住后文", skill)
        self.assertIn("不能把“读过”当成“使用过”", skill)
        self.assertIn("案例与钩子是成文输入", content_writing)
        self.assertIn("重新打开全文再继续", content_writing)

    def test_every_writing_delivery_shows_references_and_sources(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        prewriting = (PROJECT_ROOT / "references" / "prewriting-research.md").read_text(
            encoding="utf-8"
        )
        article = (PROJECT_ROOT / "references" / "article-from-practice.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("三个代码块之后固定展示两部分", skill)
        self.assertIn("本次创作参考", skill)
        self.assertIn("本次信息来源", skill)
        self.assertIn("固定的信息来源列表", prewriting)
        self.assertIn("固定展示本次创作参考和信息来源", article)
        self.assertNotIn("没有使用参考时不生成这个部分", skill)
        self.assertNotIn("写作说明和参考路径按需提供", article)

    def test_promotional_copy_is_not_replaced_by_an_unrequested_plan(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (PROJECT_ROOT / "README.en.md").read_text(encoding="utf-8")
        readme_ja = (PROJECT_ROOT / "README.ja.md").read_text(encoding="utf-8")

        self.assertIn("用户要求具体文字时直接完成文字", skill)
        self.assertIn("明确要文字时直接交付成稿", readme)
        self.assertIn("asks for copy receives finished copy directly", readme_en)
        self.assertIn("告知文を求められた場合は完成稿を直接返し", readme_ja)
        self.assertIn("不重新确认用户已经给出的数字、日期、条件或结论", readme)
        self.assertIn("they do not re-check supplied numbers, dates, conditions, or conclusions", readme_en)
        self.assertIn("すでに提示された数値、日付、条件、結論を再確認しません", readme_ja)
        self.assertNotIn("新宣发请求默认先交付方案", readme)
        self.assertNotIn("新宣发请求默认先给可确认方案", readme)

    def test_writing_search_only_discovers_missing_material_before_drafting(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        prewriting = (PROJECT_ROOT / "references" / "prewriting-research.md").read_text(
            encoding="utf-8"
        )
        natural_writing = (PROJECT_ROOT / "references" / "natural-writing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("写作前联网只寻找用户材料没有提供", skill)
        self.assertIn("每个查询都从当前材料尚未回答的问题出发", skill)
        self.assertIn("不在这里重新确认", prewriting)
        self.assertIn("不能用核对已有事实填补", prewriting)
        self.assertIn("事实核对只在完整草稿已经存在后开始", natural_writing)
        self.assertIn("只与用户材料对照是否准确转述", natural_writing)

    def test_public_writing_keeps_propagation_as_the_shared_goal(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        natural_writing = (PROJECT_ROOT / "references" / "natural-writing.md").read_text(
            encoding="utf-8"
        )
        prewriting = (PROJECT_ROOT / "references" / "prewriting-research.md").read_text(
            encoding="utf-8"
        )
        publication = (
            PROJECT_ROOT / "references" / "publication-requirements.md"
        ).read_text(encoding="utf-8")
        article = (PROJECT_ROOT / "references" / "article-from-practice.md").read_text(
            encoding="utf-8"
        )
        github_short = (
            PROJECT_ROOT / "references" / "github-project-short-content.md"
        ).read_text(encoding="utf-8")
        github_list = (
            PROJECT_ROOT / "references" / "github-project-list.md"
        ).read_text(encoding="utf-8")
        cases = (PROJECT_ROOT / "references" / "content-case-library.md").read_text(
            encoding="utf-8"
        )
        hooks = (PROJECT_ROOT / "references" / "hook-library.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("用户要可发布文字时，先完成传播", skill)
        self.assertIn("第 1 步只读取成品指令来生产任务合同", skill)
        self.assertIn("可发布文字的任务合同只写一句话", skill)
        self.assertIn("公开动作沿用用户的动词", skill)
        self.assertIn("不能再接入另一行的动词", skill)
        self.assertIn("看见对象、变化与主要利益，并愿意了解、访问或参与", skill)
        self.assertIn("不会自动把写作任务改成评估或决策", skill)
        self.assertIn("正文不新增资金配置、交易仓位和是否参与的建议", skill)
        self.assertIn("任务合同通过这次对照后立即封口", skill)
        self.assertIn("后续步骤不能再给合同增加目标", skill)
        self.assertIn("所有准备公开阅读", content_writing)
        self.assertIn("第一目标都是传播", content_writing)
        self.assertIn("简单、直白、立即进入主题本身就是有效表达", content_writing)
        self.assertIn("对象本身的利益、变化、结果或真实使用机会", content_writing)
        self.assertIn("短内容先完整说出对象、主要利益和参与结果", content_writing)
        self.assertIn("这一个行动段落就是相应事实的全部展开", content_writing)
        self.assertIn("不再添加另一句平台口径或未来更新说明", content_writing)
        self.assertIn("所有公开文字", natural_writing)
        self.assertIn("用一句话写出读者最可能转述的内容", natural_writing)
        self.assertIn("只承担对象亮相、主要利益、参与动作或结果收束", natural_writing)
        self.assertIn("最后一句单独检查", natural_writing)
        self.assertIn("返回内容成文重写", natural_writing)
        self.assertIn("公开文章和 Newsletter", article)
        self.assertIn("后续每一部分都为同一个重点增加", article)
        self.assertIn("作为可独立发布的项目介绍", github_short)
        self.assertIn("公开清单首先让读者迅速知道", github_list)
        self.assertIn("与相应传播任务一致的案例", cases)
        self.assertIn("同题材但写作任务不同的原文不进入", cases)
        self.assertIn("正面介绍、推荐和活动发布先浏览", cases)
        self.assertIn("先读取已经封口的任务合同", prewriting)
        self.assertIn("搜索问题只从对应一行选择", prewriting)
        self.assertIn("金融活动的写作搜索不承担是否持有、卖出、开仓或配置资金的判断", prewriting)
        self.assertIn("活动发布型短内容使用同一条内容关系", publication)
        self.assertIn("不新增是否开仓、怎样配置资金或是否参加的建议", publication)
        self.assertIn("不再回头强调账户、字段和计算方式", publication)
        self.assertIn("不再追加平台口径、后续更新或以其它数据为准的句子", publication)
        self.assertIn("第一句直接进入主题就是完整开头", hooks)
        self.assertIn("不能只因为读过原文就在交付时列出名称", content_writing)

    def test_ordinary_writing_context_does_not_repeat_review_language(self) -> None:
        paths = [
            PROJECT_ROOT / "SKILL.md",
            PROJECT_ROOT / "references" / "private-knowledge-library.md",
            PROJECT_ROOT / "references" / "personal-writing-memory.md",
            PROJECT_ROOT / "references" / "prewriting-research.md",
            PROJECT_ROOT / "references" / "content-case-library.md",
            PROJECT_ROOT / "references" / "hook-library.md",
            PROJECT_ROOT / "references" / "content-writing.md",
            PROJECT_ROOT / "references" / "natural-writing.md",
            PROJECT_ROOT / "references" / "publication-requirements.md",
            PROJECT_ROOT / "references" / "article-from-practice.md",
            PROJECT_ROOT / "references" / "github-project-short-content.md",
            PROJECT_ROOT / "references" / "github-project-list.md",
        ]
        active_context = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        for term in ("风险", "误解", "误读", "限制", "提醒", "承诺", "防止"):
            self.assertNotIn(term, active_context)

    def test_default_writing_does_not_use_repeated_rhetorical_shells_as_viewpoint(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        natural_writing = (PROJECT_ROOT / "references" / "natural-writing.md").read_text(
            encoding="utf-8"
        )
        content_audit = (PROJECT_ROOT / "references" / "content-audit.md").read_text(
            encoding="utf-8"
        )
        cases = (PROJECT_ROOT / "references" / "content-case-library.md").read_text(
            encoding="utf-8"
        )
        hooks = (PROJECT_ROOT / "references" / "hook-library.md").read_text(
            encoding="utf-8"
        )
        active_contract = "\n".join(
            (skill, content_writing, natural_writing, content_audit, cases, hooks)
        )

        self.assertIn("观点从当前对象的原因、先后、条件、动作和后果中长出来", skill)
        self.assertIn("不能把共同外壳变成当前成品的默认句式", skill)
        self.assertIn("不靠制造一个空泛旧观点来衬托结论", content_writing)
        self.assertIn("不同内容反复套用同一种修辞外壳", natural_writing)
        self.assertIn("句式已经代替事实推进", natural_writing)
        self.assertIn("默认成稿复查", content_audit)
        self.assertIn("不把共同句式当成当前成品的模板", cases)
        self.assertIn("不同的开头作用", hooks)
        self.assertNotIn("禁止使用“不是……而是……”", active_contract)
        self.assertNotIn("每篇最多使用一次", active_contract)

    def test_reference_use_separates_content_value_from_style_quality(self) -> None:
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        cases = (PROJECT_ROOT / "references" / "content-case-library.md").read_text(
            encoding="utf-8"
        )
        hooks = (PROJECT_ROOT / "references" / "hook-library.md").read_text(
            encoding="utf-8"
        )
        active_contract = "\n".join((skill, content_writing, cases, hooks))

        self.assertIn("最后才用题材缩小范围", skill)
        self.assertIn("跨题材寻找公开动作和推进关系一致的原文", skill)
        self.assertIn("入库只说明这是一份可读的完整原文", cases)
        self.assertIn("钩子被保存，只说明这段连续原文", hooks)
        self.assertIn("完整读入代表已经理解原文", content_writing)
        self.assertIn("实际有用的内容作用", content_writing)
        self.assertNotIn("参考质量一般时跳过", active_contract)
        self.assertNotIn("案例语气不好时停止", active_contract)

    def test_default_review_catches_overdesigned_structure_and_ai_closing(self) -> None:
        content_writing = (PROJECT_ROOT / "references" / "content-writing.md").read_text(
            encoding="utf-8"
        )
        natural_writing = (PROJECT_ROOT / "references" / "natural-writing.md").read_text(
            encoding="utf-8"
        )
        active_contract = "\n".join((content_writing, natural_writing))

        self.assertIn("不能替所有事实重新命名、逐项映射数据", content_writing)
        self.assertIn("材料没有提供作者真实行动时", content_writing)
        self.assertIn("正文没有形成一套评估体系时", content_writing)
        self.assertIn("一个比喻替所有事实重新命名", natural_writing)
        self.assertIn("结尾单独和前一段连起来读", natural_writing)
        self.assertIn("结尾临时出现作者观察姿态", natural_writing)
        self.assertNotIn("禁止使用比喻", active_contract)
        self.assertNotIn("禁止使用第一人称", active_contract)


if __name__ == "__main__":
    unittest.main()
