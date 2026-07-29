"""已归档的 DeepSeek 写作入口测试，不参与当前测试发现。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.deepseek_content_writer import (
    MODEL,
    SYSTEM_PROMPT,
    WriterError,
    build_payload,
    build_quality_revision_packet,
    content_quality_issues,
    generate_deliverable,
    parse_env_file,
    validate_packet,
)


def valid_packet() -> dict:
    return {
        "action": "draft",
        "content_mode": "general",
        "subject": "subject-token",
        "core_message": ["primary-token", "secondary-token"],
        "content_truth": "truth-token",
        "audience": "audience-token",
        "deliverable": "deliverable-token",
        "creative_direction": "creative-token",
        "hard_constraints": ["constraint-token"],
    }


def valid_distribution_plan() -> dict:
    return {
        "primary_reader": {
            "role": "reader-role-token",
            "context": "reader-context-token",
            "job": "reader-job-token",
            "pain": "reader-pain-token",
            "desired_outcome": "reader-outcome-token",
            "awareness": "reader-awareness-token",
            "objection": "",
        },
        "reader_action": "reader-action-token",
        "content_atoms": [
            {
                "id": "atom-1",
                "type": "claim",
                "content": "atom-content-token",
                "source_boundary": "atom-source-token",
            }
        ],
        "portfolio": [
            {
                "id": "post-1",
                "platform": "platform-token",
                "format": "format-token",
                "job": "post-job-token",
                "angle": "post-angle-token",
                "atom_ids": ["atom-1"],
                "hook_strategy": "hook-token",
                "value_delivery": "value-token",
                "engagement": "engagement-token",
                "cta": {
                    "mode": "none",
                    "promise": "",
                    "destination_status": "not_needed",
                    "destination": "",
                },
            }
        ],
        "platform_checks": [
            {
                "platform": "platform-token",
                "status": "not_required",
                "checked_at": "",
                "sources": [],
                "constraints": [],
            }
        ],
        "trend": {
            "status": "not_requested",
            "bridge": "",
            "sources": [],
        },
    }


def valid_editorial_position() -> dict:
    return {
        "source": "user-confirmed-series-position-token",
        "position": "position-token",
        "selection_rules": ["selection-token"],
        "claim_boundaries": ["boundary-token"],
    }


def valid_voice_contract() -> dict:
    return {
        "narrative_driver": "driver-token",
        "point_of_view": "point-of-view-token",
        "opening": "opening-token",
        "layout": "layout-token",
        "media_role": "media-role-token",
        "humor_mechanism": "humor-token",
        "ending": "ending-token",
        "avoid": ["avoid-token"],
        "stable_traits": ["stable-token"],
        "sample_specific_traits": ["sample-token"],
    }


class DeepSeekContentWriterTests(unittest.TestCase):
    def test_payload_uses_requested_model_with_default_thinking(self) -> None:
        payload = build_payload(validate_packet(valid_packet()), 1234)

        self.assertEqual(payload["model"], MODEL)
        self.assertNotIn("thinking", payload)
        self.assertNotIn("reasoning_effort", payload)
        self.assertEqual(payload["max_tokens"], 1234)
        self.assertNotIn("temperature", payload)
        self.assertNotIn("top_p", payload)
        self.assertIn("不是 A，而是 B", SYSTEM_PROMPT)

    def test_hard_constraints_can_be_empty(self) -> None:
        packet = valid_packet()
        packet["hard_constraints"] = []

        validated = validate_packet(packet)

        self.assertEqual(validated["hard_constraints"], [])

    def test_editorial_position_and_voice_contract_reach_model_payload(
        self,
    ) -> None:
        packet = valid_packet()
        packet["editorial_position"] = valid_editorial_position()
        packet["voice_contract"] = valid_voice_contract()

        validated = validate_packet(packet)
        payload = build_payload(validated, 1234)
        user_message = payload["messages"][1]["content"]

        self.assertEqual(
            validated["editorial_position"]["position"], "position-token"
        )
        self.assertEqual(
            validated["voice_contract"]["stable_traits"], ["stable-token"]
        )
        self.assertIn('"editorial_position"', user_message)
        self.assertIn('"voice_contract"', user_message)

    def test_editorial_position_requires_selection_rule(self) -> None:
        packet = valid_packet()
        packet["editorial_position"] = valid_editorial_position()
        packet["editorial_position"]["selection_rules"] = []

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_voice_contract_rejects_trait_confidence_overlap(self) -> None:
        packet = valid_packet()
        packet["voice_contract"] = valid_voice_contract()
        packet["voice_contract"]["sample_specific_traits"] = ["stable-token"]

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_content_mode_is_required(self) -> None:
        packet = valid_packet()
        packet.pop("content_mode")

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_general_mode_rejects_distribution_plan(self) -> None:
        packet = valid_packet()
        packet["distribution_plan"] = valid_distribution_plan()

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_github_project_short_mode_rejects_distribution_plan(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "github_project_short"
        packet["distribution_plan"] = valid_distribution_plan()

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_github_project_short_mode_reaches_model_payload(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "github_project_short"
        packet["subject"] = "project-subject-token"
        packet["content_truth"] = "official-project-truth-token"
        packet["creative_direction"] = "series-style-token"

        validated = validate_packet(packet)
        payload = build_payload(validated, 1234)
        user_message = payload["messages"][1]["content"]

        self.assertEqual(validated["content_mode"], "github_project_short")
        self.assertIn("content_mode=github_project_short", SYSTEM_PROMPT)
        self.assertIn("star 这个词", SYSTEM_PROMPT)
        self.assertIn("project-subject-token", user_message)
        self.assertIn("official-project-truth-token", user_message)
        self.assertIn("series-style-token", user_message)

    def test_social_distribution_requires_plan(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_social_distribution_plan_reaches_model_payload(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"
        packet["distribution_plan"] = valid_distribution_plan()

        validated = validate_packet(packet)
        payload = build_payload(validated, 1234)
        user_message = payload["messages"][1]["content"]

        self.assertEqual(validated["distribution_plan"]["portfolio"][0]["id"], "post-1")
        self.assertIn('"distribution_plan"', user_message)
        self.assertIn("atom-content-token", user_message)
        self.assertIn("post-angle-token", user_message)

    def test_distribution_plan_rejects_unknown_atom_reference(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"
        plan = valid_distribution_plan()
        plan["portfolio"][0]["atom_ids"] = ["missing-atom"]
        packet["distribution_plan"] = plan

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_enabled_cta_requires_real_or_missing_destination_state(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"
        plan = valid_distribution_plan()
        plan["portfolio"][0]["cta"] = {
            "mode": "first_comment_or_reply",
            "promise": "resource-token",
            "destination_status": "provided",
            "destination": "",
        }
        packet["distribution_plan"] = plan

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_verified_platform_check_requires_current_evidence(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"
        plan = valid_distribution_plan()
        plan["platform_checks"][0]["status"] = "verified"
        packet["distribution_plan"] = plan

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_forbidden_contrast_template_is_detected(self) -> None:
        issues = content_quality_issues("需要修正的缺口不是速度，是来源边界。")

        self.assertEqual(issues, ["正文使用了禁用的预制二元对照句式"])

    def test_plain_negative_statement_does_not_trigger_contrast_gate(self) -> None:
        self.assertEqual(content_quality_issues("这个结论不是来源原话。"), [])

    def test_verified_direct_quote_can_keep_source_wording(self) -> None:
        packet = valid_packet()
        packet["content_truth"] = "原文写道：“学习不是记住，而是能在任务中调用。”"
        content = "原文写道：“学习不是记住，而是能在任务中调用。”"

        self.assertEqual(content_quality_issues(content, packet), [])

    def test_quality_revision_preserves_distribution_plan(self) -> None:
        packet = valid_packet()
        packet["content_mode"] = "social_distribution"
        packet["distribution_plan"] = valid_distribution_plan()
        packet["editorial_position"] = valid_editorial_position()
        packet["voice_contract"] = valid_voice_contract()
        validated = validate_packet(packet)

        revision = build_quality_revision_packet(
            validated,
            "需要修订的正文",
            ["正文使用了禁用的预制二元对照句式"],
        )

        self.assertEqual(revision["action"], "revise")
        self.assertEqual(revision["current_text"], "需要修订的正文")
        self.assertEqual(
            revision["distribution_plan"],
            validated["distribution_plan"],
        )
        self.assertEqual(
            revision["editorial_position"],
            validated["editorial_position"],
        )
        self.assertEqual(
            revision["voice_contract"],
            validated["voice_contract"],
        )

    @patch("scripts.deepseek_content_writer.generate_content")
    def test_quality_gate_revises_once_before_delivery(self, generate_mock) -> None:
        generate_mock.side_effect = [
            (
                "需要修正的缺口不是速度，是来源边界。",
                {"usage": {"total_tokens": 10}},
            ),
            ("真正需要修正的是来源边界。", {"usage": {"total_tokens": 8}}),
        ]
        packet = validate_packet(valid_packet())

        content, metadata = generate_deliverable(
            packet,
            api_key="key-token",
            max_tokens=100,
            timeout=10,
        )

        self.assertEqual(content, "真正需要修正的是来源边界。")
        self.assertEqual(generate_mock.call_count, 2)
        revision_packet = generate_mock.call_args_list[1].args[0]
        self.assertEqual(revision_packet["action"], "revise")
        self.assertEqual(metadata["quality_gate"]["attempts"], 2)

    def test_subject_and_core_message_are_required(self) -> None:
        without_subject = valid_packet()
        without_subject.pop("subject")
        without_core = valid_packet()
        without_core["core_message"] = []

        with self.assertRaises(WriterError):
            validate_packet(without_subject)
        with self.assertRaises(WriterError):
            validate_packet(without_core)

    def test_legacy_packet_fields_are_rejected(self) -> None:
        packet = valid_packet()
        packet["voice"] = "legacy-token"
        packet["constraints"] = []

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_revision_requires_current_text_and_request(self) -> None:
        packet = valid_packet()
        packet["action"] = "revise"

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_draft_rejects_revision_fields(self) -> None:
        packet = valid_packet()
        packet["current_text"] = "current-token"

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_unknown_packet_fields_are_rejected(self) -> None:
        packet = valid_packet()
        packet["extra"] = "extra-token"

        with self.assertRaises(WriterError):
            validate_packet(packet)

    def test_env_parser_reads_key_without_exposing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deepseek.env"
            path.write_text(
                "# local only\nDEEPSEEK_API_KEY='secret-token'\n",
                encoding="utf-8",
            )

            values = parse_env_file(path)

        self.assertEqual(values, {"DEEPSEEK_API_KEY": "secret-token"})


if __name__ == "__main__":
    unittest.main()
