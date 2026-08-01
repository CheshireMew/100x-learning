from __future__ import annotations

import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from scripts.content_case_library import main as case_main
from scripts.writing_delivery import (
    DeliveryError,
    SEARCH_SCHEMA_PATH,
    main as delivery_main,
    render_delivery,
    validate_json_schema,
    validate_record,
)


FULL_QUERY = (
    "让不懂技术的人迅速感到项目变化，用短句直接推进，"
    "随后用紧凑的并列事实增加力度"
)
HOOK_QUERY = (
    "先点出读者熟悉的痛点，再由项目带来的明确变化直接解决，"
    "让人共鸣并继续读"
)


def _receipt(asset: str, query: str) -> dict[str, object]:
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = case_main(
            [
                "search",
                "--asset",
                asset,
                "--content-type",
                "项目与产品介绍",
                "--query",
                query,
                "--limit",
                "3",
                "--format",
                "json",
            ]
        )
    if code != 0:
        raise RuntimeError(stderr.getvalue())
    return json.loads(stdout.getvalue())


def _not_adopted_full(candidate_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "status": "not_adopted",
        "reason": "候选需要另一种内容关系，不能改善当前讲法。",
        "counterfactual": "移开候选后，正文的措辞、推进和收束都不变。",
        "source_excerpt": "",
        "source_mechanism": "",
        "draft_excerpt": "",
        "effect": "",
        "distinct_from_template": False,
    }


def _not_adopted_hook(candidate_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "status": "not_adopted",
        "reason": "必须关系虽然接近，但没有让当前两句更清楚或更紧凑。",
        "source_excerpt": "",
        "source_opening_action": "",
        "required_relation_mappings": [],
        "optional_amplifier_mappings": [],
        "opening": "",
        "continuation": "",
        "improvement_dimensions": [],
        "effect": "",
    }


def _record() -> dict[str, object]:
    full_receipt = _receipt("short", FULL_QUERY)
    hook_receipt = _receipt("hook", HOOK_QUERY)
    draft = "普通人现在可以直接完成这件事。项目会把结果保存在本地，之后还能继续修改。"
    return {
        "schema_version": 1,
        "artifact": {
            "format": "product",
            "target_reader": "第一次接触这个项目的普通读者",
            "primary_reader_result_id": "result-1",
            "editorial_choice": "先写读者获得的变化，再用项目事实证明，不把内部流程塞进开头。",
            "opening": "普通人现在可以直接完成这件事。",
            "continuation": "项目会把结果保存在本地，之后还能继续修改。",
            "reader_paraphrase": "不用先理解内部实现，也知道自己可以直接完成并继续修改。",
            "single_reader_result": True,
            "requires_internal_term_explanation": False,
            "draft": draft,
        },
        "materials": [
            {
                "material_id": "result-1",
                "kind": "reader_result",
                "content": "普通人能够直接完成任务，结果之后还能继续修改",
                "source_location": "current_material",
                "placement": "lead",
                "reason": "这是目标读者最先能感受到的变化。",
            },
            {
                "material_id": "proof-1",
                "kind": "proof",
                "content": "项目把结果保存在本地",
                "source_location": "current_material",
                "placement": "proof",
                "reason": "它证明结果不是一次性展示。",
            },
            {
                "material_id": "mechanism-1",
                "kind": "internal_mechanism",
                "content": "项目内部使用统一工作流",
                "source_location": "current_material",
                "placement": "omitted",
                "reason": "内部流程不会增加普通读者对结果的理解。",
            },
        ],
        "facts": [
            {
                "statement": "项目把结果保存在本地，之后仍可修改",
                "source_location": "current_material",
                "source_kind": "current_material",
                "draft_excerpt": "项目会把结果保存在本地，之后还能继续修改",
                "effect": "它支撑了正文的可继续使用结果。",
            }
        ],
        "full_case_search": full_receipt,
        "full_case_decisions": [
            _not_adopted_full(candidate["candidate_id"])
            for candidate in full_receipt["candidates"][:2]
        ],
        "hook_search": hook_receipt,
        "hook_decisions": [
            _not_adopted_hook(candidate["candidate_id"])
            for candidate in hook_receipt["candidates"][:2]
        ],
        "language_decisions": [
            {
                "source_expression": "统一工作流",
                "reader_expression": "还能继续修改",
                "effect": "把内部机制改成读者能够观察到的后续动作。",
            }
        ],
        "omissions": [
            {
                "content": "内部组件清单",
                "reason": "它会挤占第一屏，但不会增加读者对主要变化的理解。",
            }
        ],
        "voice_sources": [],
        "format_requirements": ["一条短内容"],
        "promotion_contract": "",
    }


class WritingDeliveryTests(unittest.TestCase):
    def test_json_search_output_is_a_schema_valid_real_receipt(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = case_main(
                [
                    "search",
                    "--asset",
                    "hook",
                    "--content-type",
                    "项目与产品介绍",
                    "--query",
                    HOOK_QUERY,
                    "--limit",
                    "3",
                    "--format",
                    "json",
                ]
            )

        self.assertEqual(0, code)
        self.assertEqual("", stderr.getvalue())
        receipt = json.loads(stdout.getvalue())
        validate_json_schema(receipt, SEARCH_SCHEMA_PATH, label="receipt")
        self.assertEqual("hook", receipt["request"]["assets"][0])
        self.assertGreaterEqual(len(receipt["candidates"]), 2)
        self.assertTrue(
            all(candidate["case_file"] for candidate in receipt["candidates"])
        )
        self.assertTrue(
            all(candidate["source"] for candidate in receipt["candidates"])
        )

    def test_real_search_receipts_reach_the_validator_and_renderer(self) -> None:
        record = _record()

        validate_record(record)
        rendered = render_delivery(record)

        self.assertIn("## 写作成品", rendered)
        self.assertIn("## 写作说明", rendered)
        self.assertIn("### 完整内容案例", rendered)
        self.assertIn("### 钩子", rendered)
        self.assertIn("已检索，未采用", rendered)
        first_case = record["full_case_search"]["candidates"][0]
        self.assertIn(first_case["case_file"], rendered)
        self.assertIn(first_case["source"], rendered)
        self.assertNotIn("。。", rendered)

    def test_public_producer_stdout_reaches_public_consumer_stdin(self) -> None:
        record = _record()
        stdin = StringIO(json.dumps(record, ensure_ascii=False))
        stdout = StringIO()
        stderr = StringIO()

        with patch("sys.stdin", stdin), redirect_stdout(stdout), redirect_stderr(stderr):
            code = delivery_main(["render", "--record", "-"])

        self.assertEqual(0, code)
        self.assertEqual("", stderr.getvalue())
        self.assertIn(record["artifact"]["draft"], stdout.getvalue())
        self.assertIn("## 写作说明", stdout.getvalue())

    def test_modified_search_receipt_cannot_reach_the_consumer(self) -> None:
        record = _record()
        record["hook_search"]["candidates"][0]["source"] = "https://example.com/fake"

        with self.assertRaisesRegex(DeliveryError, "不是当前案例库与正式检索器生成"):
            validate_record(record)

    def test_full_case_cannot_be_claimed_without_source_and_draft_evidence(self) -> None:
        record = _record()
        candidate = record["full_case_search"]["candidates"][0]
        record["full_case_decisions"][0] = {
            "candidate_id": candidate["candidate_id"],
            "status": "adopted",
            "reason": "候选改变了正文。",
            "counterfactual": "移开后正文会失去这一推进。",
            "source_excerpt": "这段文字并不存在于来源",
            "source_mechanism": "用具体结果进入",
            "draft_excerpt": "普通人现在可以直接完成这件事",
            "effect": "让开头更直接。",
            "distinct_from_template": True,
        }

        with self.assertRaisesRegex(DeliveryError, "不在案例原文中"):
            validate_record(record)

    def test_full_case_adoption_reaches_the_rendered_explanation(self) -> None:
        record = _record()
        candidate = record["full_case_search"]["candidates"][0]
        record["full_case_decisions"][0] = {
            "candidate_id": candidate["candidate_id"],
            "status": "adopted",
            "reason": "候选的短句推进改善了当前开头。",
            "counterfactual": "移开后，正文不会再用短句先交付结果。",
            "source_excerpt": candidate["text"][:20],
            "source_mechanism": "先用短句交付结果，再由项目事实承接",
            "draft_excerpt": "普通人现在可以直接完成这件事",
            "effect": "开头先让读者看到变化。",
            "distinct_from_template": True,
        }

        rendered = render_delivery(record)

        self.assertIn("已检索并采用", rendered)
        self.assertIn(candidate["case_file"], rendered)
        self.assertIn("不是专项模板或当前材料本来就会产生", rendered)

    def test_two_full_cases_can_change_different_draft_positions(self) -> None:
        record = _record()
        first, second = record["full_case_search"]["candidates"][:2]
        record["full_case_decisions"][:2] = [
            {
                "candidate_id": first["candidate_id"],
                "status": "adopted",
                "reason": "候选改善了第一句的进入方式。",
                "counterfactual": "移开后，第一句不会先交付普通人得到的变化。",
                "source_excerpt": first["text"][:20],
                "source_mechanism": "先用短句交付读者结果",
                "draft_excerpt": "普通人现在可以直接完成这件事",
                "effect": "让读者先知道自己能得到什么。",
                "distinct_from_template": True,
            },
            {
                "candidate_id": second["candidate_id"],
                "status": "adopted",
                "reason": "候选改善了证明材料的承接。",
                "counterfactual": "移开后，本地保存和继续修改不会被压进同一句证明。",
                "source_excerpt": second["text"][:20],
                "source_mechanism": "用紧凑事实承接前句结果",
                "draft_excerpt": "项目会把结果保存在本地，之后还能继续修改",
                "effect": "让第二句直接兑现第一句。",
                "distinct_from_template": True,
            },
        ]

        rendered = render_delivery(record)

        self.assertEqual(2, rendered.count("已检索并采用"))
        self.assertIn(first["case_file"], rendered)
        self.assertIn(second["case_file"], rendered)

    def test_two_candidates_require_two_real_decisions(self) -> None:
        record = _record()
        record["full_case_decisions"] = record["full_case_decisions"][:1]

        with self.assertRaisesRegex(DeliveryError, "至少要实际比较 2 个"):
            validate_record(record)

    def test_adopted_hook_maps_all_required_relations_without_optional_amplifiers(self) -> None:
        record = _record()
        candidate = record["hook_search"]["candidates"][0]
        record["hook_decisions"][0] = {
            "candidate_id": candidate["candidate_id"],
            "status": "adopted",
            "reason": "候选让读者先看到变化，再由项目事实承接。",
            "source_excerpt": candidate["text"][:20],
            "source_opening_action": candidate["hook_techniques"][0],
            "required_relation_mappings": [
                {
                    "relation": relation,
                    "material_ids": ["result-1", "proof-1"],
                }
                for relation in candidate["required_relations"]
            ],
            "optional_amplifier_mappings": [],
            "opening": record["artifact"]["opening"],
            "continuation": record["artifact"]["continuation"],
            "improvement_dimensions": ["clarity"],
            "effect": "读者先知道自己得到什么，再看到项目如何兑现。",
        }

        validate_record(record)

    def test_adopted_hook_action_must_come_from_the_candidate(self) -> None:
        record = _record()
        candidate = record["hook_search"]["candidates"][0]
        record["hook_decisions"][0] = {
            "candidate_id": candidate["candidate_id"],
            "status": "adopted",
            "reason": "候选改变了开头。",
            "source_excerpt": candidate["text"][:20],
            "source_opening_action": "随意填写的动作",
            "required_relation_mappings": [
                {"relation": relation, "material_ids": ["result-1"]}
                for relation in candidate["required_relations"]
            ],
            "optional_amplifier_mappings": [],
            "opening": record["artifact"]["opening"],
            "continuation": record["artifact"]["continuation"],
            "improvement_dimensions": ["clarity"],
            "effect": "开头更清楚。",
        }

        with self.assertRaisesRegex(DeliveryError, "开头动作"):
            validate_record(record)

    def test_opening_and_continuation_must_be_the_delivered_first_two_sentences(self) -> None:
        record = _record()
        record["artifact"]["opening"] = "正文中不存在的开头。"

        with self.assertRaisesRegex(DeliveryError, "实际第一句"):
            validate_record(record)

    def test_internal_mechanism_cannot_be_placed_in_the_opening(self) -> None:
        record = _record()
        record["materials"][2]["placement"] = "lead"

        with self.assertRaisesRegex(DeliveryError, "证明和内部机制必须后置或省略"):
            validate_record(record)

    def test_language_conversion_must_start_from_real_material(self) -> None:
        record = _record()
        record["language_decisions"][0]["source_expression"] = "材料里不存在的术语"

        with self.assertRaisesRegex(DeliveryError, "不在正式材料中"):
            validate_record(record)

    def test_copy_only_still_validates_the_complete_record(self) -> None:
        rendered = render_delivery(_record(), include_explanation=False)

        self.assertIn("## 写作成品", rendered)
        self.assertNotIn("## 写作说明", rendered)


if __name__ == "__main__":
    unittest.main()
