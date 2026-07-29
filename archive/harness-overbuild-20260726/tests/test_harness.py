from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness.policies import (
    TOOL_ROUTES,
    validate_content_audit,
    validate_distribution_contract,
    validate_evidence_bundle,
    validate_task_contract,
    validate_writing_packet,
    validate_write_plan,
)
from harness.knowledge import validate_knowledge_note
from harness.repository import validate_repository
from harness.content_cases import load_library, search_library


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_KB = ROOT / "tests" / "fixtures" / "kb"


def valid_task() -> dict:
    return {
        "task_type": "topic_research",
        "purpose": "形成快速理解",
        "deliverable_type": "answer",
        "depth": "quick",
        "stage": "planning",
        "source_mode": "topic",
        "knowledge_base": {
            "available": True,
            "read_required": True,
            "read_completed": False,
            "write_requested": False,
            "write_authorized": False,
        },
        "research": {
            "external_started": False,
            "high_impact_claims": False,
            "verification_planned": False,
        },
        "tool_route": {
            "selected": "web",
        },
    }


def valid_writing_task() -> dict:
    task = valid_task()
    task.update(
        {
            "task_type": "research_writing",
            "deliverable_type": "edit",
            "source_mode": "material",
            "purpose": "比较样稿并提炼作者声音",
            "writing": {
                "action": "voice_analysis",
                "scope": [
                    "voice",
                    "structure",
                    "rhythm",
                    "language",
                    "humor",
                    "density",
                ],
                "research_requested": False,
                "voice_sample_available": True,
                "narrative_basis": "lived_chronology",
                "experience_material": "not_required",
                "existing_materials": "not_required",
            },
        }
    )
    task["knowledge_base"].update(
        {"read_required": True, "read_completed": False}
    )
    task["tool_route"]["selected"] = "none"
    return task


def produced_writing_examples(
    *,
    asset: str,
    content_type: str | None = None,
    include_hook: bool = False,
) -> dict:
    cases, issues = load_library()
    if issues:
        raise AssertionError(issues)
    candidates = [
        case
        for case in cases
        if case.asset == asset
        and (content_type is None or case.content_type == content_type)
    ]
    if not candidates:
        raise AssertionError(
            f"missing {asset} case for content type {content_type}"
        )
    source = candidates[0]
    assets = ["hook", asset] if include_hook else [asset]
    hits = search_library(
        writing_task=source.writing_task,
        topics=source.topics[:1],
        structures=source.structure[:1],
        assets=assets,
        content_type=source.content_type,
        limit=len(assets),
    )
    return {
        "writing_task": source.writing_task,
        "content_type": source.content_type,
        "topics": list(source.topics[:1]),
        "structure": list(source.structure[:1]),
        "references": [
            str(hit.case.relative_path)
            for hit in hits
        ],
    }


def valid_writing_packet() -> dict:
    return {
        "action": "draft",
        "viral_requested": False,
        "narrative_basis": "lived_chronology",
        "shareable_point": "从真实实践中说明 AI 怎样帮助安排训练",
        "writing_job": {
            "object": "个人训练实践",
            "angle": "从真实问题走到当前判断",
            "deliverable": "article",
            "audience": "想用 AI 改善生活安排的普通读者",
            "core_information": ["真实触发", "尝试与阻力", "当前选择"],
            "requirements": ["保留第一人称经历", "使用短段落"],
        },
        "content_truth": [
            {
                "statement": "作者把器械和动作数据交给 Codex 设计方案",
                "status": "direct",
                "source": "published user article",
            }
        ],
        "writing_templates": [
            "references/content-writing.md",
            "references/article-from-practice.md",
        ],
        "writing_examples": produced_writing_examples(asset="article"),
        "author_voice": {
            "sources": [
                {
                    "reference": "published user article",
                    "authorship": "user",
                    "verification": "published",
                },
                {
                    "reference": (
                        "System Knowledge/60-Systems/Writing/"
                        "style-guide/voice.md"
                    ),
                    "authorship": "system_profile",
                    "verification": "maintained_profile",
                },
            ],
            "signals": [
                "第一人称按真实发生顺序推进",
                "短段落与明确判断并存",
                "认真理由后允许自然自嘲",
            ],
            "preserved_choices": [],
        },
        "experience_events": [
            {
                "stage": "trigger",
                "detail": "发现健康问题后决定减肥",
                "source": {
                    "reference": "published user article",
                    "authorship": "user",
                    "verification": "published",
                },
            },
            {
                "stage": "friction",
                "detail": "跟视频练三天后疼痛且动作太复杂",
                "source": {
                    "reference": "published user article",
                    "authorship": "user",
                    "verification": "published",
                },
            },
            {
                "stage": "choice",
                "detail": "把器械和动作数据集交给 Codex 设计方案",
                "source": {
                    "reference": "published user article",
                    "authorship": "user",
                    "verification": "published",
                },
            },
            {
                "stage": "judgment",
                "detail": "认为这次用 Codex 安排生活习惯是成功尝试",
                "source": {
                    "reference": "published user article",
                    "authorship": "user",
                    "verification": "published",
                },
            },
        ],
    }


def valid_github_writing_packet() -> dict:
    packet = valid_writing_packet()
    packet.update(
        {
            "narrative_basis": "research_explanation",
            "shareable_point": "把长视频变成可精确修改的文字剪辑",
            "writing_job": {
                "object": "project-a",
                "angle": "让创作者看见完整使用结果",
                "deliverable": "github_project_short",
                "audience": "需要处理长视频的创作者",
                "core_information": [
                    "视频转写",
                    "按文字定位并删除片段",
                    "项目入口",
                ],
                "requirements": [
                    "使用当前用户确认的直接语气",
                    "结尾给出项目入口",
                ],
            },
            "writing_templates": [
                "references/content-writing.md",
                "references/github-project-short-content.md",
            ],
            "writing_examples": produced_writing_examples(
                asset="short",
                content_type="项目与产品介绍",
            ),
            "author_voice": {
                "sources": [
                    {
                        "reference": "current user instruction",
                        "authorship": "user",
                        "verification": "current_user_input",
                    }
                ],
                "signals": [
                    "直接写用户能得到的结果",
                    "能力讲完后给出鲜明判断",
                ],
                "preserved_choices": [],
            },
            "experience_events": [],
            "github_project": {
                "project_name": "project-a",
                "project_url": "https://github.com/example/project-a",
                "reader": "需要处理长视频的创作者",
                "problem": "人工定位和剪掉片段很慢",
                "user_result": "通过文字定位并完成视频粗剪",
                "project_role": "本地视频文字化剪辑工具",
                "capabilities": ["转写视频", "按文字定位和删除片段"],
                "series_relationship": "独立项目",
                "presentation": {
                    "opening_task": "先让创作者看见省掉手工定位的结果",
                    "body_shape": "paragraphs",
                    "link_placement": "结尾",
                    "ending_task": "给出项目入口",
                },
            },
        }
    )
    return packet


def valid_content_audit() -> dict:
    return {
        "mode": "content_only",
        "severity_threshold": "material",
        "scope": [
            "authenticity",
            "core_claim",
            "logic",
            "reader_action",
            "structure",
        ],
        "fact_check_requested": False,
        "external_research_started": False,
        "author_voice_protected": True,
        "findings": [
            {
                "severity": "material",
                "category": "structure",
                "issue": "第三天训练内容与第二天重复，文章没有展示腿部方案",
                "root_cause": "三分化方案展示不完整",
                "impact": "读者无法从正文确认三分化是否完整呈现",
                "minimal_fix": "把第三天标题或对应截图改为腿部训练",
                "action": "fix",
            }
        ],
    }


class RepositoryTests(unittest.TestCase):
    def test_repository_doctor_passes(self) -> None:
        report = validate_repository(ROOT)
        self.assertTrue(report.ok, report.to_dict())

    def test_active_writing_route_has_no_automatic_prose_gate(self) -> None:
        active_files = [
            ROOT / "harness" / "policies.py",
            ROOT / "references" / "content-writing.md",
            ROOT / "references" / "github-project-short-content.md",
        ]
        active_text = "\n".join(
            path.read_text(encoding="utf-8") for path in active_files
        )
        for retired_symbol in (
            "FORBIDDEN_CONTRAST_RE",
            "content_quality_issues",
            "build_quality_revision_packet",
            "generate_deliverable",
        ):
            self.assertNotIn(retired_symbol, active_text)


class DistributionGateTests(unittest.TestCase):
    def test_invalid_distribution_plan_is_reported(self) -> None:
        report = validate_distribution_contract({})

        self.assertIn(
            "distribution.invalid_plan",
            {issue.code for issue in report.issues},
        )


class TaskContractTests(unittest.TestCase):
    def test_valid_contract_passes(self) -> None:
        self.assertTrue(validate_task_contract(valid_task()).ok)

    def test_external_research_cannot_skip_required_local_read(self) -> None:
        task = valid_task()
        task["research"]["external_started"] = True
        report = validate_task_contract(task)
        self.assertIn(
            "task.external_before_local",
            {issue.code for issue in report.issues},
        )

    def test_research_tool_routes_are_generic(self) -> None:
        self.assertEqual(TOOL_ROUTES, {"none", "local_only", "web"})

        task = valid_task()
        task["purpose"] = "核对当前产品规则与官方说明"
        task["research"]["external_started"] = True
        task["knowledge_base"]["read_completed"] = True
        report = validate_task_contract(task)
        self.assertTrue(report.ok, report.to_dict())

    def test_retired_provider_route_and_fields_are_rejected(self) -> None:
        task = valid_task()
        task["tool_route"]["selected"] = "gr" + "ok"
        report = validate_task_contract(task)
        self.assertIn(
            "contract.invalid_enum",
            {issue.code for issue in report.issues},
        )

        for field in (
            "gr" + "ok_requested",
            "x" + "_required",
            "fallback" + "_reason",
        ):
            task = valid_task()
            task["tool_route"][field] = False
            report = validate_task_contract(task)
            self.assertIn(
                "contract.unexpected_fields",
                {issue.code for issue in report.issues},
            )

    def test_high_impact_claim_requires_verification_plan(self) -> None:
        task = valid_task()
        task["research"].update(
            {
                "high_impact_claims": True,
                "verification_planned": False,
            }
        )
        report = validate_task_contract(task)
        self.assertIn(
            "task.high_impact_without_verification",
            {issue.code for issue in report.issues},
        )

    def test_voice_analysis_contract_passes_without_research(self) -> None:
        report = validate_task_contract(valid_writing_task())
        self.assertTrue(report.ok, report.to_dict())

    def test_voice_analysis_cannot_start_unrequested_research(self) -> None:
        task = valid_writing_task()
        task["research"]["external_started"] = True
        report = validate_task_contract(task)
        self.assertIn(
            "task.writing_research_not_requested",
            {issue.code for issue in report.issues},
        )

    def test_voice_analysis_requires_verified_sample(self) -> None:
        task = valid_writing_task()
        task["writing"]["voice_sample_available"] = False
        report = validate_task_contract(task)
        self.assertIn(
            "task.voice_analysis_without_sample",
            {issue.code for issue in report.issues},
        )

    def test_lived_draft_requires_real_experience_material(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "draft",
                "scope": ["voice", "structure", "content"],
                "experience_material": "missing",
                "existing_materials": "searched",
            }
        )
        report = validate_task_contract(task)
        self.assertIn(
            "task.lived_draft_without_experience",
            {issue.code for issue in report.issues},
        )

    def test_missing_experience_cannot_be_declared_before_archive_search(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "article_structure",
                "scope": ["voice", "structure", "content"],
                "experience_material": "missing",
                "existing_materials": "pending",
            }
        )
        report = validate_task_contract(task)
        self.assertIn(
            "task.experience_gap_before_archive_search",
            {issue.code for issue in report.issues},
        )

    def test_lived_draft_with_real_experience_material_passes(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "draft",
                "scope": ["voice", "structure", "content"],
                "experience_material": "sufficient",
                "existing_materials": "searched",
            }
        )
        report = validate_task_contract(task)
        self.assertTrue(report.ok, report.to_dict())

    def test_explicit_fact_check_scope_can_use_research(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "fact_check",
                "scope": ["facts", "citations"],
                "research_requested": True,
                "voice_sample_available": False,
                "narrative_basis": "research_explanation",
            }
        )
        task["research"].update(
            {
                "external_started": True,
                "high_impact_claims": True,
                "verification_planned": True,
            }
        )
        task["knowledge_base"]["read_completed"] = True
        task["tool_route"]["selected"] = "web"
        report = validate_task_contract(task)
        self.assertTrue(report.ok, report.to_dict())

    def test_content_audit_can_run_without_fact_research(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "content_audit",
                "scope": ["content", "logic", "structure", "voice"],
                "research_requested": False,
            }
        )
        report = validate_task_contract(task)
        self.assertTrue(report.ok, report.to_dict())

    def test_content_audit_requires_content_scope(self) -> None:
        task = valid_writing_task()
        task["writing"].update(
            {
                "action": "content_audit",
                "scope": ["voice"],
            }
        )
        report = validate_task_contract(task)
        self.assertIn(
            "task.content_audit_without_content_scope",
            {issue.code for issue in report.issues},
        )


class WriteGateTests(unittest.TestCase):
    def test_existing_topic_must_be_updated(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Existing Topic",
            "aliases": [],
            "operations": [
                {
                    "action": "update",
                    "path": "10-Knowledge/Test/Existing Topic.md",
                }
            ],
        }
        self.assertTrue(validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB).ok)

    def test_parallel_topic_creation_is_rejected(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Existing Topic",
            "aliases": [],
            "operations": [
                {
                    "action": "create",
                    "path": "10-Knowledge/Test/Existing Topic New.md",
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn("write.parallel_topic_source", {issue.code for issue in report.issues})

    def test_write_without_authorization_is_rejected(self) -> None:
        plan = {
            "write_authorized": False,
            "topic": "New Topic",
            "aliases": [],
            "operations": [
                {"action": "create", "path": "10-Knowledge/Test/New Topic.md"}
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn("write.not_authorized", {issue.code for issue in report.issues})

    def test_knowledge_root_cannot_be_overridden_by_input(self) -> None:
        plan = {
            "kb_root": str(FIXTURE_KB),
            "write_authorized": True,
            "topic": "Existing Topic",
            "aliases": [],
            "operations": [
                {
                    "action": "update",
                    "path": "10-Knowledge/Test/Existing Topic.md",
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn("write.kb_root_override", {issue.code for issue in report.issues})

    def test_duplicate_source_url_is_rejected(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Source ingestion",
            "aliases": [],
            "operations": [
                {
                    "action": "create",
                    "path": "20-Sources/Test/Another Source.md",
                    "source_identity": {
                        "url": "https://example.com/existing-source",
                    },
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn("write.duplicate_source", {issue.code for issue in report.issues})

    def test_source_write_requires_identity(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Source ingestion",
            "aliases": [],
            "operations": [
                {"action": "create", "path": "20-Sources/Test/New Source.md"}
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn("write.missing_source_identity", {issue.code for issue in report.issues})

    def test_frontmatter_alias_identifies_existing_topic(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Existing Topic Alias",
            "aliases": [],
            "operations": [
                {
                    "action": "update",
                    "path": "10-Knowledge/Test/Existing Topic.md",
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertTrue(report.ok, report.to_dict())

    def test_agent_draft_cannot_be_written_to_outputs(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Draft article",
            "aliases": [],
            "operations": [
                {
                    "action": "create",
                    "path": "40-Outputs/Writing/Articles/Draft article.md",
                    "writing_artifact": {
                        "state": "draft",
                        "source": "agent-draft",
                    },
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertIn(
            "write.unverified_writing_output",
            {issue.code for issue in report.issues},
        )

    def test_published_article_can_be_written_to_outputs(self) -> None:
        plan = {
            "write_authorized": True,
            "topic": "Published article",
            "aliases": [],
            "operations": [
                {
                    "action": "create",
                    "path": "40-Outputs/Writing/Articles/Published article.md",
                    "writing_artifact": {
                        "state": "final",
                        "source": "published-article",
                    },
                }
            ],
        }
        report = validate_write_plan(plan, ROOT, knowledge_root=FIXTURE_KB)
        self.assertTrue(report.ok, report.to_dict())


class WritingPacketTests(unittest.TestCase):
    def test_real_voice_template_and_article_example_packet_passes(self) -> None:
        report = validate_writing_packet(valid_writing_packet())
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.details["example_assets"], ["article"])
        self.assertEqual(
            report.details["template_references"],
            [
                "references/article-from-practice.md",
                "references/content-writing.md",
            ],
        )
        self.assertGreater(report.details["author_voice_source_count"], 0)

    def test_github_project_packet_always_has_author_voice(self) -> None:
        report = validate_writing_packet(valid_github_writing_packet())
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.details["deliverable"], "github_project_short")
        self.assertEqual(report.details["example_assets"], ["short"])
        self.assertEqual(report.details["voice_signal_count"], 2)

    def test_github_project_requires_its_specialized_contract(self) -> None:
        packet = valid_github_writing_packet()
        packet.pop("github_project")
        report = validate_writing_packet(packet)
        self.assertIn(
            "contract.invalid_object",
            {issue.code for issue in report.issues},
        )

    def test_github_project_requires_both_writing_templates(self) -> None:
        packet = valid_github_writing_packet()
        packet["writing_templates"] = ["references/content-writing.md"]
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.template_set_mismatch",
            {issue.code for issue in report.issues},
        )

    def test_github_project_requires_same_type_full_short_example(self) -> None:
        packet = valid_github_writing_packet()
        cases, issues = load_library()
        self.assertFalse(issues, issues)
        hook = next(case for case in cases if case.asset == "hook")
        packet["writing_examples"]["references"] = [
            str(hook.relative_path)
        ]
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.same_type_body_example_required",
            {issue.code for issue in report.issues},
        )

    def test_explicit_viral_request_requires_hook_and_body_examples(self) -> None:
        packet = valid_github_writing_packet()
        packet["viral_requested"] = True
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.viral_hook_example_required",
            {issue.code for issue in report.issues},
        )

        packet["writing_examples"] = produced_writing_examples(
            asset="short",
            content_type="项目与产品介绍",
            include_hook=True,
        )
        report = validate_writing_packet(packet)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.details["example_assets"], ["hook", "short"])

    def test_invalid_example_path_is_rejected(self) -> None:
        packet = valid_writing_packet()
        packet["writing_examples"]["references"] = ["missing-case.md"]
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.invalid_example_reference",
            {issue.code for issue in report.issues},
        )

    def test_search_output_is_consumed_as_the_real_writing_input(self) -> None:
        packet = valid_github_writing_packet()
        produced = produced_writing_examples(
            asset="short",
            content_type="项目与产品介绍",
        )
        packet["writing_examples"] = produced
        report = validate_writing_packet(packet)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(
            report.details["example_reference_count"],
            len(produced["references"]),
        )
        for reference in produced["references"]:
            self.assertTrue((ROOT / reference).is_file())

    def test_cli_producer_to_validator_chain_uses_real_full_cases(self) -> None:
        search = subprocess.run(
            [
                sys.executable,
                "scripts/content_case_library.py",
                "search",
                "--writing-task",
                "介绍开源项目",
                "--content-type",
                "项目与产品介绍",
                "--topic",
                "AI",
                "--structure",
                "用户结果",
                "--asset",
                "hook",
                "--asset",
                "short",
                "--limit",
                "2",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(search.returncode, 0, search.stderr)
        produced_cases = json.loads(search.stdout)
        self.assertEqual(
            {item["asset"] for item in produced_cases},
            {"hook", "short"},
        )
        self.assertTrue(
            all(item["original_text"].strip() for item in produced_cases)
        )

        packet = valid_github_writing_packet()
        packet["viral_requested"] = True
        packet["writing_examples"] = {
            "writing_task": "介绍开源项目",
            "content_type": "项目与产品介绍",
            "topics": ["AI"],
            "structure": ["用户结果"],
            "references": [item["path"] for item in produced_cases],
        }
        validation = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness",
                "validate-writing",
                "-",
            ],
            cwd=ROOT,
            input=json.dumps(packet, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validation.returncode, 0, validation.stdout)
        payload = json.loads(validation.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["details"]["example_assets"], ["hook", "short"])

    def test_article_cannot_use_a_short_body_example(self) -> None:
        packet = valid_writing_packet()
        packet["writing_examples"] = produced_writing_examples(
            asset="short",
            content_type="项目与产品介绍",
        )
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.same_type_body_example_required",
            {issue.code for issue in report.issues},
        )
        self.assertIn(
            "writing.unexpected_example_asset",
            {issue.code for issue in report.issues},
        )

    def test_body_example_content_type_must_match_the_declared_type(self) -> None:
        packet = valid_github_writing_packet()
        packet["writing_examples"]["content_type"] = "概念与机制解释"
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.example_content_type_mismatch",
            {issue.code for issue in report.issues},
        )

    def test_lived_article_without_source_events_is_rejected(self) -> None:
        packet = valid_writing_packet()
        packet["experience_events"] = []
        report = validate_writing_packet(packet)
        codes = {issue.code for issue in report.issues}
        self.assertIn("writing.missing_experience_trigger", codes)
        self.assertIn("writing.missing_experience_process", codes)
        self.assertIn("writing.missing_experience_outcome", codes)

    def test_edit_uses_current_text_and_current_requirements(self) -> None:
        packet = valid_writing_packet()
        packet["action"] = "edit"
        packet["writing_job"]["current_text_reference"] = (
            "current user-confirmed draft"
        )
        packet["writing_job"]["requirements"] = [
            "保留当前第一段",
            "把第三段改成项目实际结果",
        ]
        report = validate_writing_packet(packet)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.details["requirement_count"], 2)

    def test_edit_requires_the_current_text_reference(self) -> None:
        packet = valid_writing_packet()
        packet["action"] = "edit"
        report = validate_writing_packet(packet)
        self.assertIn(
            "contract.required_text",
            {issue.code for issue in report.issues},
        )

    def test_every_writing_packet_requires_user_voice_source(self) -> None:
        packet = valid_github_writing_packet()
        packet["author_voice"]["sources"] = []
        report = validate_writing_packet(packet)
        codes = {issue.code for issue in report.issues}
        self.assertIn("writing.missing_author_voice_sources", codes)
        self.assertIn("writing.user_voice_source_required", codes)

    def test_profile_can_supplement_but_not_replace_user_voice(self) -> None:
        packet = valid_github_writing_packet()
        packet["author_voice"]["sources"] = [
            {
                "reference": (
                    "System Knowledge/60-Systems/Writing/"
                    "style-guide/voice.md"
                ),
                "authorship": "system_profile",
                "verification": "maintained_profile",
            }
        ]
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.user_voice_source_required",
            {issue.code for issue in report.issues},
        )

    def test_author_voice_keeps_a_small_positive_signal_set(self) -> None:
        packet = valid_github_writing_packet()
        packet["author_voice"]["signals"] = [
            "signal-1",
            "signal-2",
            "signal-3",
            "signal-4",
            "signal-5",
            "signal-6",
        ]
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.too_many_voice_signals",
            {issue.code for issue in report.issues},
        )

    def test_packet_schema_rejects_parallel_internal_contracts(self) -> None:
        packet = valid_github_writing_packet()
        packet["parallel_contract"] = {"requirements": []}
        report = validate_writing_packet(packet)
        self.assertIn(
            "contract.unexpected_fields",
            {issue.code for issue in report.issues},
        )

    def test_thread_keeps_its_distribution_plan_in_the_same_input(self) -> None:
        packet = valid_github_writing_packet()
        packet["writing_job"]["deliverable"] = "thread"
        packet["writing_templates"] = [
            "references/content-writing.md",
            "references/social-content-distribution.md",
        ]
        packet.pop("github_project")
        report = validate_writing_packet(packet)
        self.assertIn(
            "writing.thread_distribution_plan_required",
            {issue.code for issue in report.issues},
        )


class ContentAuditTests(unittest.TestCase):
    def test_material_only_content_audit_passes(self) -> None:
        report = validate_content_audit(valid_content_audit())
        self.assertTrue(report.ok, report.to_dict())

    def test_audit_with_no_material_findings_passes(self) -> None:
        audit = valid_content_audit()
        audit["findings"] = []
        report = validate_content_audit(audit)
        self.assertTrue(report.ok, report.to_dict())

    def test_minor_finding_is_rejected_by_default(self) -> None:
        audit = valid_content_audit()
        audit["findings"] = [
            {
                "severity": "minor",
                "category": "format",
                "issue": "一个标点可以更统一",
                "root_cause": "标点风格不统一",
                "impact": "不影响理解",
                "minimal_fix": "调整标点",
                "action": "fix",
            }
        ]
        audit["scope"].append("format")
        report = validate_content_audit(audit)
        codes = {issue.code for issue in report.issues}
        self.assertIn("audit.finding_below_threshold", codes)
        self.assertIn("audit.minor_finding_outside_line_edit", codes)

    def test_minor_finding_is_allowed_for_explicit_line_edit(self) -> None:
        audit = valid_content_audit()
        audit.update(
            {
                "mode": "line_edit",
                "severity_threshold": "minor",
                "scope": ["language", "format"],
                "findings": [
                    {
                        "severity": "minor",
                        "category": "language",
                        "issue": "一个错字",
                        "root_cause": "局部录入错误",
                        "impact": "逐字校对范围内需要修正",
                        "minimal_fix": "改正错字",
                        "action": "fix",
                    }
                ],
            }
        )
        report = validate_content_audit(audit)
        self.assertTrue(report.ok, report.to_dict())

    def test_unrequested_research_is_rejected(self) -> None:
        audit = valid_content_audit()
        audit["external_research_started"] = True
        report = validate_content_audit(audit)
        codes = {issue.code for issue in report.issues}
        self.assertIn("audit.unrequested_external_research", codes)
        self.assertIn("audit.content_only_used_research", codes)

    def test_fact_audit_mode_requires_explicit_request(self) -> None:
        audit = valid_content_audit()
        audit["mode"] = "content_and_fact"
        report = validate_content_audit(audit)
        self.assertIn(
            "audit.fact_mode_without_request",
            {issue.code for issue in report.issues},
        )

    def test_finding_outside_requested_scope_is_rejected(self) -> None:
        audit = valid_content_audit()
        audit["findings"][0]["category"] = "voice"
        report = validate_content_audit(audit)
        self.assertIn(
            "audit.finding_outside_scope",
            {issue.code for issue in report.issues},
        )

    def test_same_root_cause_must_be_merged(self) -> None:
        audit = valid_content_audit()
        duplicate = dict(audit["findings"][0])
        duplicate["issue"] = "结尾再次遗漏腿部训练"
        audit["findings"].append(duplicate)
        report = validate_content_audit(audit)
        self.assertIn(
            "audit.duplicate_root_cause",
            {issue.code for issue in report.issues},
        )

    def test_repeated_verbal_habit_can_be_a_material_finding(self) -> None:
        audit = valid_content_audit()
        audit["scope"].append("verbal_habit")
        audit["findings"] = [
            {
                "severity": "material",
                "category": "verbal_habit",
                "issue": "连续多个段落都用‘我感觉’起句",
                "root_cause": "主观标记词重复削弱判断",
                "impact": "原本明确的结论显得犹豫，段落节奏也开始单调",
                "minimal_fix": "保留真正表达感受的一处，其余明确判断直接陈述",
                "action": "fix",
            }
        ]
        report = validate_content_audit(audit)
        self.assertTrue(report.ok, report.to_dict())


class KnowledgeNoteTests(unittest.TestCase):
    def test_ai_readable_knowledge_note_passes(self) -> None:
        note = FIXTURE_KB / "10-Knowledge" / "Test" / "Existing Topic.md"
        report = validate_knowledge_note(note, FIXTURE_KB)
        self.assertTrue(report.ok, report.to_dict())

    def test_extensionless_full_path_link_to_dotted_filename_passes(self) -> None:
        note = FIXTURE_KB / "10-Knowledge" / "Test" / "Dotted Link Topic.md"
        report = validate_knowledge_note(note, FIXTURE_KB)
        self.assertTrue(report.ok, report.to_dict())

    def test_invalid_knowledge_note_reports_contract_failures(self) -> None:
        note = FIXTURE_KB / "10-Knowledge" / "Test" / "Invalid Note.md"
        report = validate_knowledge_note(note, FIXTURE_KB)
        codes = {issue.code for issue in report.issues}
        self.assertIn("note.missing_frontmatter_field", codes)
        self.assertIn("note.title_filename_mismatch", codes)
        self.assertIn("note.missing_provenance", codes)
        self.assertIn("note.missing_boundaries", codes)


class EvidenceGateTests(unittest.TestCase):
    def test_summary_cannot_support_exact_quote(self) -> None:
        bundle = {
            "claims": [
                {
                    "claim": "一段精确引语",
                    "impact": "normal",
                    "is_quote": True,
                    "time_sensitive": False,
                    "sources": [
                        {
                            "url": "https://example.com/summary",
                            "role": "case",
                            "access": "summary",
                            "authority": "secondary",
                            "verified": True,
                        }
                    ],
                }
            ]
        }
        report = validate_evidence_bundle(bundle)
        codes = {issue.code for issue in report.issues}
        self.assertIn("evidence.quote_without_original", codes)

    def test_high_impact_current_claim_needs_primary_dated_source(self) -> None:
        bundle = {
            "claims": [
                {
                    "claim": "当前规则",
                    "impact": "high",
                    "is_quote": False,
                    "time_sensitive": True,
                    "sources": [
                        {
                            "url": "https://example.gov/rule",
                            "role": "evidence",
                            "access": "direct",
                            "authority": "official",
                            "verified": True,
                            "checked_at": "2026-07-13",
                        }
                    ],
                }
            ]
        }
        self.assertTrue(validate_evidence_bundle(bundle).ok)


if __name__ == "__main__":
    unittest.main()
