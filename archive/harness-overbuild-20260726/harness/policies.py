from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .content_cases import (
    ContentCaseError,
    parse_case,
)
from .distribution import DistributionPlanError, validate_distribution_plan
from .knowledge import knowledge_note_terms
from .result import ValidationReport


TASK_TYPES = {
    "material_extraction",
    "learning_diagnosis",
    "topic_research",
    "concept_explanation",
    "knowledge_persistence",
    "practice_conversion",
    "research_writing",
    "out_of_scope",
}

DELIVERABLE_TYPES = {
    "answer",
    "key_segments",
    "learning_diagnosis",
    "research_materials",
    "content_route",
    "article_structure",
    "draft",
    "edit",
    "content_audit",
    "simulation",
    "tool",
    "plan",
    "knowledge_update",
}
DEPTHS = {"quick", "writing_or_decision", "deep"}
STAGES = {"planning", "research", "synthesis", "write", "complete"}
SOURCE_MODES = {"material", "topic", "existing_knowledge", "mixed", "none"}
TOOL_ROUTES = {"none", "local_only", "web"}
TASK_WRITING_ACTIONS = {
    "content_route",
    "article_structure",
    "draft",
    "edit",
    "voice_analysis",
    "content_audit",
    "fact_check",
}
CONTENT_PRODUCTION_ACTIONS = {
    "content_route",
    "article_structure",
    "draft",
    "edit",
}
WRITING_JOB_TEXT_FIELDS = {
    "object",
    "angle",
    "audience",
}
WRITING_DELIVERABLES = {
    "short_post",
    "thread",
    "short_copy",
    "github_project_short",
    "article",
    "newsletter",
}
CONTENT_TRUTH_STATUSES = {
    "direct",
    "project_claim",
    "observed",
    "unconfirmed",
}
GITHUB_PROJECT_TEXT_FIELDS = {
    "project_name",
    "project_url",
    "reader",
    "problem",
    "user_result",
    "project_role",
    "series_relationship",
}
GITHUB_PRESENTATION_TEXT_FIELDS = {
    "opening_task",
    "link_placement",
    "ending_task",
}
GITHUB_BODY_SHAPES = {"paragraphs", "list", "mixed"}
GITHUB_STAR_STATUSES = {"verified", "unavailable"}
WRITING_EXAMPLE_ASSETS = {"hook", "short", "article"}
WRITING_TEMPLATE_BY_DELIVERABLE = {
    "short_post": {
        "references/content-writing.md",
    },
    "thread": {
        "references/content-writing.md",
        "references/social-content-distribution.md",
    },
    "short_copy": {
        "references/content-writing.md",
    },
    "github_project_short": {
        "references/content-writing.md",
        "references/github-project-short-content.md",
    },
    "article": {
        "references/content-writing.md",
        "references/article-from-practice.md",
    },
    "newsletter": {
        "references/content-writing.md",
        "references/article-from-practice.md",
    },
}
WRITING_SCOPES = {
    "voice",
    "structure",
    "rhythm",
    "language",
    "humor",
    "density",
    "content",
    "authenticity",
    "logic",
    "reader_action",
    "facts",
    "citations",
}
NARRATIVE_BASES = {
    "lived_chronology",
    "problem_progression",
    "research_explanation",
}
EXPERIENCE_MATERIAL_STATES = {"not_required", "sufficient", "missing"}
EXISTING_MATERIAL_STATES = {"not_required", "pending", "searched", "unavailable"}
WRITING_SOURCE_AUTHORSHIPS = {"user", "system_profile"}
WRITING_SOURCE_VERIFICATIONS = {
    "current_user_input",
    "user_confirmed",
    "published",
    "maintained_profile",
}
USER_SOURCE_VERIFICATIONS = {
    "current_user_input",
    "user_confirmed",
    "published",
}
EXPERIENCE_STAGES = {
    "trigger",
    "attempt",
    "friction",
    "choice",
    "result",
    "judgment",
}
AUDIT_MODES = {"content_only", "content_and_fact", "line_edit"}
AUDIT_SEVERITIES = {"blocking", "material", "minor"}
AUDIT_SEVERITY_LEVELS = {"blocking": 3, "material": 2, "minor": 1}
AUDIT_CATEGORIES = {
    "authenticity",
    "core_claim",
    "logic",
    "key_fact",
    "reader_action",
    "structure",
    "voice",
    "language",
    "format",
    "verbal_habit",
}
AUDIT_ACTIONS = {"fix", "ask"}
WRITE_ACTIONS = {"create", "update"}
WRITING_ARTIFACT_STATES = {"draft", "final"}
WRITING_ARTIFACT_SOURCES = {
    "agent-draft",
    "user-draft",
    "user-confirmed",
    "published-article",
}
SOURCE_ROLES = {
    "definition",
    "evidence",
    "explanation",
    "case",
    "counterargument",
    "practice",
    "question",
}
SOURCE_ACCESS = {"direct", "summary", "inference"}
SOURCE_AUTHORITIES = {"official", "primary", "secondary", "personal", "unknown"}
HIGH_IMPACT_AUTHORITIES = {"official", "primary"}
HOME_DIRECTORY_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def _mapping(value: Any, field: str, report: ValidationReport) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    report.error("contract.invalid_object", "必须是对象", field)
    return {}


def _required_text(data: dict[str, Any], name: str, report: ValidationReport) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        report.error("contract.required_text", "必须是非空字符串", name)
        return ""
    return value.strip()


def _enum_value(
    data: dict[str, Any], name: str, allowed: set[str], report: ValidationReport
) -> str:
    value = data.get(name)
    if value not in allowed:
        report.error(
            "contract.invalid_enum",
            f"必须是以下值之一：{', '.join(sorted(allowed))}",
            name,
        )
        return ""
    return str(value)


def _bool_value(
    data: dict[str, Any], name: str, report: ValidationReport, default: bool = False
) -> bool:
    if name not in data:
        report.error("contract.required_boolean", "缺少必需的布尔值", name)
        return default
    value = data[name]
    if not isinstance(value, bool):
        report.error("contract.invalid_boolean", "必须是布尔值", name)
        return default
    return value


def _enum_list(
    data: dict[str, Any], name: str, allowed: set[str], report: ValidationReport
) -> set[str]:
    value = data.get(name)
    if not isinstance(value, list) or not value:
        report.error("contract.required_list", "必须是非空数组", name)
        return set()
    if not all(isinstance(item, str) and item in allowed for item in value):
        report.error(
            "contract.invalid_list_value",
            f"数组项必须是以下值之一：{', '.join(sorted(allowed))}",
            name,
        )
        return set()
    if len(value) != len(set(value)):
        report.error("contract.duplicate_list_value", "数组中不能有重复项", name)
    return set(value)


def _text_list(
    data: dict[str, Any],
    name: str,
    report: ValidationReport,
    *,
    required: bool,
) -> set[str]:
    value = data.get(name)
    if not isinstance(value, list) or (required and not value):
        requirement = "非空数组" if required else "数组"
        report.error("contract.required_list", f"必须是{requirement}", name)
        return set()
    if not all(isinstance(item, str) and item.strip() for item in value):
        report.error(
            "contract.invalid_list_value",
            "数组项必须是非空字符串",
            name,
        )
        return set()
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        report.error("contract.duplicate_list_value", "数组中不能有重复项", name)
    return set(normalized)


def _reject_unexpected_fields(
    data: dict[str, Any],
    allowed: set[str],
    name: str,
    report: ValidationReport,
) -> None:
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        report.error(
            "contract.unexpected_fields",
            "当前合同包含未定义字段：" + "、".join(unexpected),
            name,
        )


def _validate_content_truth(
    value: Any, report: ValidationReport
) -> tuple[int, set[str]]:
    if not isinstance(value, list) or not value:
        report.error(
            "writing.missing_content_truth",
            "成文动作必须提供至少一条带状态与来源的内容真源",
            "content_truth",
        )
        return 0, set()

    statuses: set[str] = set()
    for index, item in enumerate(value):
        field = f"content_truth.{index}"
        fact = _mapping(item, field, report)
        _required_text(fact, "statement", report)
        status = _enum_value(
            fact,
            "status",
            CONTENT_TRUTH_STATUSES,
            report,
        )
        _required_text(fact, "source", report)
        if status:
            statuses.add(status)
    return len(value), statuses


def _validate_github_project(value: Any, report: ValidationReport) -> None:
    project = _mapping(value, "github_project", report)
    for field_name in sorted(GITHUB_PROJECT_TEXT_FIELDS):
        _required_text(project, field_name, report)

    project_url = project.get("project_url")
    if isinstance(project_url, str) and project_url.strip():
        parsed = urlparse(project_url.strip())
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
            report.error(
                "writing.invalid_github_project_url",
                "project_url 必须是 github.com 上可直接访问的仓库地址",
                "github_project.project_url",
            )

    _text_list(project, "capabilities", report, required=True)

    if "star" in project:
        star = _mapping(project.get("star"), "github_project.star", report)
        star_status = _enum_value(
            star,
            "status",
            GITHUB_STAR_STATUSES,
            report,
        )
        checked_on = _required_text(star, "checked_on", report)
        if checked_on:
            try:
                date.fromisoformat(checked_on)
            except ValueError:
                report.error(
                    "writing.invalid_star_check_date",
                    "checked_on 必须是 YYYY-MM-DD 日期",
                    "github_project.star.checked_on",
                )
        _required_text(star, "source", report)
        if star_status == "verified":
            count = star.get("count")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                report.error(
                    "writing.invalid_star_count",
                    "已核对的 star 数量必须是大于等于 0 的整数",
                    "github_project.star.count",
                )
        elif star_status == "unavailable":
            _required_text(star, "reason", report)
            if "count" in star:
                report.error(
                    "writing.unavailable_star_has_count",
                    "无法读取 star 时不填写 count",
                    "github_project.star.count",
                )

    presentation = _mapping(
        project.get("presentation"),
        "github_project.presentation",
        report,
    )
    for field_name in sorted(GITHUB_PRESENTATION_TEXT_FIELDS):
        _required_text(presentation, field_name, report)
    _enum_value(
        presentation,
        "body_shape",
        GITHUB_BODY_SHAPES,
        report,
    )


def validate_distribution_contract(data: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    try:
        plan = validate_distribution_plan(data)
    except DistributionPlanError as exc:
        report.error(
            "distribution.invalid_plan",
            str(exc),
            "distribution_plan",
        )
        return report

    report.details.update(
        {
            "content_atom_count": len(plan["content_atoms"]),
            "portfolio_count": len(plan["portfolio"]),
            "platform_check_count": len(plan["platform_checks"]),
            "trend_status": plan["trend"]["status"],
        }
    )
    return report


def validate_task_contract(data: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    task_type = _enum_value(data, "task_type", TASK_TYPES, report)
    deliverable = _enum_value(data, "deliverable_type", DELIVERABLE_TYPES, report)
    _enum_value(data, "depth", DEPTHS, report)
    stage = _enum_value(data, "stage", STAGES, report)
    _enum_value(data, "source_mode", SOURCE_MODES, report)
    _required_text(data, "purpose", report)

    knowledge_base = _mapping(data.get("knowledge_base", {}), "knowledge_base", report)
    kb_available = _bool_value(knowledge_base, "available", report)
    read_required = _bool_value(knowledge_base, "read_required", report)
    read_completed = _bool_value(knowledge_base, "read_completed", report)
    write_requested = _bool_value(knowledge_base, "write_requested", report)
    write_authorized = _bool_value(knowledge_base, "write_authorized", report)

    research = _mapping(data.get("research", {}), "research", report)
    external_started = _bool_value(research, "external_started", report)
    high_impact = _bool_value(research, "high_impact_claims", report)
    verification_planned = _bool_value(research, "verification_planned", report)

    route = _mapping(data.get("tool_route", {}), "tool_route", report)
    _reject_unexpected_fields(
        route,
        {"selected"},
        "tool_route",
        report,
    )
    _enum_value(route, "selected", TOOL_ROUTES, report)

    writing_action = ""
    writing_scope: set[str] = set()
    existing_materials = ""
    if task_type == "research_writing":
        writing = _mapping(data.get("writing", {}), "writing", report)
        writing_action = _enum_value(
            writing, "action", TASK_WRITING_ACTIONS, report
        )
        writing_scope = _enum_list(
            writing, "scope", WRITING_SCOPES, report
        )
        research_requested = _bool_value(writing, "research_requested", report)
        voice_sample_available = _bool_value(
            writing, "voice_sample_available", report
        )
        narrative_basis = _enum_value(
            writing, "narrative_basis", NARRATIVE_BASES, report
        )
        experience_material = _enum_value(
            writing,
            "experience_material",
            EXPERIENCE_MATERIAL_STATES,
            report,
        )
        existing_materials = _enum_value(
            writing,
            "existing_materials",
            EXISTING_MATERIAL_STATES,
            report,
        )

        if external_started and not research_requested:
            report.error(
                "task.writing_research_not_requested",
                "写作任务未声明用户要求研究，不能开始外部研究",
                "research.external_started",
            )
        if "facts" in writing_scope and not research_requested:
            report.error(
                "task.facts_without_research_request",
                "写作范围包含事实核查时，必须声明用户已经要求研究或核查",
                "writing.research_requested",
            )
        if high_impact and "facts" not in writing_scope:
            report.error(
                "task.claims_outside_writing_scope",
                "当前写作范围不处理事实，不能把样稿主张登记为待核查主张",
                "research.high_impact_claims",
            )
        if writing_action == "voice_analysis":
            if "voice" not in writing_scope:
                report.error(
                    "task.voice_analysis_without_voice_scope",
                    "声音分析必须把 voice 列入写作范围",
                    "writing.scope",
                )
            if not voice_sample_available:
                report.error(
                    "task.voice_analysis_without_sample",
                    "声音分析必须已有经过作者身份与版本状态验证的用户样稿",
                    "writing.voice_sample_available",
                )
        if writing_action == "fact_check" and "facts" not in writing_scope:
            report.error(
                "task.fact_check_without_fact_scope",
                "事实核查必须把 facts 列入写作范围",
                "writing.scope",
            )
        if writing_action == "content_audit" and not writing_scope.intersection(
            {"content", "authenticity", "logic", "reader_action", "structure"}
        ):
            report.error(
                "task.content_audit_without_content_scope",
                "内容审计必须明确检查内容、真实性、逻辑、结构或读者行动中的至少一项",
                "writing.scope",
            )
        if "voice" in writing_scope and not voice_sample_available:
            report.error(
                "task.voice_scope_without_source",
                "要求延续或分析作者声音时，必须读取样稿或声音档案",
                "writing.voice_sample_available",
            )
        if (
            writing_action == "draft"
            and narrative_basis == "lived_chronology"
            and experience_material != "sufficient"
        ):
            report.error(
                "task.lived_draft_without_experience",
                "第一人称经历型文章缺少真实经历材料，不能开始起草",
                "writing.experience_material",
            )
        if (
            narrative_basis == "lived_chronology"
            and experience_material == "missing"
            and kb_available
            and existing_materials != "searched"
        ):
            report.error(
                "task.experience_gap_before_archive_search",
                "知识库可用时，必须先检索已有文章和经历材料，不能直接把经历判定为缺失并询问用户",
                "writing.existing_materials",
            )
        if existing_materials == "unavailable" and kb_available:
            report.error(
                "task.material_archive_marked_unavailable",
                "知识库可用时不能把已有材料库标为 unavailable",
                "writing.existing_materials",
            )
        if narrative_basis != "lived_chronology" and experience_material == "sufficient":
            report.warning(
                "task.unused_experience_material",
                "已有真实经历材料但叙事骨架未使用经历时间线，请确认这是有意选择",
                "writing.narrative_basis",
            )

    if write_requested and not write_authorized:
        report.error(
            "task.write_without_authorization",
            "请求包含持久化写入，但尚未取得写入授权",
            "knowledge_base.write_authorized",
        )
    if read_required and not kb_available:
        report.error(
            "task.read_without_kb",
            "知识库不可用时不能声明必须读取本地知识",
            "knowledge_base.read_required",
        )
    if deliverable == "knowledge_update" and not write_requested:
        report.error(
            "task.knowledge_update_without_write",
            "knowledge_update 交付物必须声明 write_requested",
            "knowledge_base.write_requested",
        )
    if write_requested and not kb_available:
        report.error(
            "task.write_without_kb",
            "知识库不可用时不能进入写入阶段",
            "knowledge_base.available",
        )
    if read_required and external_started and not read_completed:
        report.error(
            "task.external_before_local",
            "要求先读本地知识时，不能在完成本地读取前开始外部研究",
            "knowledge_base.read_completed",
        )
    if high_impact and not verification_planned:
        report.error(
            "task.high_impact_without_verification",
            "高影响主张必须安排核查",
            "research.verification_planned",
        )
    if stage in {"write", "complete"} and write_requested and not write_authorized:
        report.error(
            "task.invalid_write_stage",
            "没有写入授权时不能进入 write 或 complete 阶段",
            "stage",
        )
    if task_type == "out_of_scope" and write_requested:
        report.error(
            "task.out_of_scope_write",
            "未触发 Skill 的任务不能通过本 Harness 请求知识库写入",
            "task_type",
        )

    report.details.update(
        {
            "task_type": task_type,
            "deliverable_type": deliverable,
            "stage": stage,
            "writing_action": writing_action,
            "writing_scope": sorted(writing_scope),
            "existing_materials": existing_materials,
            "voice_sample_available": (
                voice_sample_available if task_type == "research_writing" else False
            ),
        }
    )
    return report


def validate_writing_packet(data: dict[str, Any]) -> ValidationReport:
    """Validate the single input used by the active writing producer.

    Every content-producing action receives content truth, the current author
    voice, the applicable templates, and full same-type examples together.
    This validator checks that production boundary. Prose quality remains a
    semantic review against those real resources and the current user request.
    """

    report = ValidationReport()
    _reject_unexpected_fields(
        data,
        {
            "action",
            "viral_requested",
            "narrative_basis",
            "shareable_point",
            "writing_job",
            "content_truth",
            "writing_templates",
            "writing_examples",
            "author_voice",
            "experience_events",
            "github_project",
            "distribution_plan",
        },
        "writing_packet",
        report,
    )

    action = _enum_value(
        data,
        "action",
        CONTENT_PRODUCTION_ACTIONS,
        report,
    )
    viral_requested = _bool_value(data, "viral_requested", report)
    narrative_basis = _enum_value(
        data,
        "narrative_basis",
        NARRATIVE_BASES,
        report,
    )
    _required_text(data, "shareable_point", report)

    writing_job = _mapping(data.get("writing_job"), "writing_job", report)
    _reject_unexpected_fields(
        writing_job,
        {
            "object",
            "angle",
            "deliverable",
            "audience",
            "core_information",
            "requirements",
            "current_text_reference",
        },
        "writing_job",
        report,
    )
    for field_name in sorted(WRITING_JOB_TEXT_FIELDS):
        _required_text(writing_job, field_name, report)
    deliverable = _enum_value(
        writing_job,
        "deliverable",
        WRITING_DELIVERABLES,
        report,
    )
    core_information = _text_list(
        writing_job,
        "core_information",
        report,
        required=True,
    )
    requirements = _text_list(
        writing_job,
        "requirements",
        report,
        required=True,
    )
    current_text_reference = writing_job.get("current_text_reference")
    if action == "edit":
        _required_text(writing_job, "current_text_reference", report)
    elif current_text_reference is not None and (
        not isinstance(current_text_reference, str)
        or not current_text_reference.strip()
    ):
        report.error(
            "writing.invalid_current_text_reference",
            "提供 current_text_reference 时必须指向当前有效正文",
            "writing_job.current_text_reference",
        )

    content_truth_count, content_truth_statuses = _validate_content_truth(
        data.get("content_truth"),
        report,
    )
    distribution_portfolio_count = 0
    if "distribution_plan" in data:
        try:
            normalized_distribution = validate_distribution_plan(
                data["distribution_plan"]
            )
        except DistributionPlanError as exc:
            report.error(
                "writing.invalid_distribution_plan",
                str(exc),
                "distribution_plan",
            )
        else:
            distribution_portfolio_count = len(
                normalized_distribution["portfolio"]
            )
    elif deliverable == "thread":
        report.error(
            "writing.thread_distribution_plan_required",
            "Thread 成文输入必须包含已经校验的平台内容组合计划",
            "distribution_plan",
        )

    template_references_value = data.get("writing_templates")
    if (
        not isinstance(template_references_value, list)
        or not template_references_value
        or not all(
            isinstance(item, str) and item.strip()
            for item in template_references_value
        )
    ):
        report.error(
            "writing.invalid_templates",
            "writing_templates 必须列出本次生产者实际读取的模板路径",
            "writing_templates",
        )
        template_references: list[str] = []
    else:
        template_references = [
            item.strip() for item in template_references_value
        ]
    if len(template_references) != len(set(template_references)):
        report.error(
            "writing.duplicate_template",
            "同一写作模板只读取一次",
            "writing_templates",
        )

    expected_templates = WRITING_TEMPLATE_BY_DELIVERABLE.get(
        deliverable,
        set(),
    )
    if set(template_references) != expected_templates:
        report.error(
            "writing.template_set_mismatch",
            "当前交付物必须同时读取基础成文模板和对应专项模板",
            "writing_templates",
        )
    project_root = Path(__file__).resolve().parents[1]
    for index, reference in enumerate(template_references):
        candidate = project_root / Path(reference)
        try:
            text = candidate.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            report.error(
                "writing.template_unavailable",
                f"写作模板不可读取：{exc}",
                f"writing_templates.{index}",
            )
            continue
        if not text.strip():
            report.error(
                "writing.empty_template",
                "写作模板不能为空",
                f"writing_templates.{index}",
            )

    examples = _mapping(
        data.get("writing_examples"),
        "writing_examples",
        report,
    )
    _reject_unexpected_fields(
        examples,
        {
            "writing_task",
            "content_type",
            "topics",
            "structure",
            "references",
        },
        "writing_examples",
        report,
    )
    _required_text(examples, "writing_task", report)
    example_content_type = _required_text(
        examples,
        "content_type",
        report,
    )
    _text_list(examples, "topics", report, required=True)
    _text_list(examples, "structure", report, required=True)

    example_references_value = examples.get("references")
    if (
        not isinstance(example_references_value, list)
        or not example_references_value
        or not all(
            isinstance(item, str) and item.strip()
            for item in example_references_value
        )
    ):
        report.error(
            "writing.invalid_example_references",
            "writing_examples.references 必须包含同类型完整案例路径",
            "writing_examples.references",
        )
        example_references: list[str] = []
    else:
        example_references = [
            item.strip() for item in example_references_value
        ]
    if len(example_references) != len(set(example_references)):
        report.error(
            "writing.duplicate_example_reference",
            "同一个完整案例只读取一次",
            "writing_examples.references",
        )

    loaded_assets: set[str] = set()
    body_content_types: set[str] = set()
    for index, reference in enumerate(example_references):
        candidate = Path(reference)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        try:
            content_case = parse_case(candidate)
        except (ContentCaseError, OSError, UnicodeError) as exc:
            report.error(
                "writing.invalid_example_reference",
                f"完整案例不可读取或结构无效：{exc}",
                f"writing_examples.references.{index}",
            )
            continue
        loaded_assets.add(content_case.asset)
        if content_case.asset in {"short", "article"}:
            body_content_types.add(content_case.content_type)

    body_asset = (
        "article"
        if deliverable in {"article", "newsletter"}
        else "short"
    )
    if body_asset not in loaded_assets:
        report.error(
            "writing.same_type_body_example_required",
            "成文生产者必须读取与交付形态对应的完整正文案例",
            "writing_examples.references",
        )
    allowed_assets = {body_asset, "hook"}
    unexpected_assets = loaded_assets - allowed_assets
    if unexpected_assets:
        report.error(
            "writing.unexpected_example_asset",
            "案例资产与当前交付形态不一致",
            "writing_examples.references",
        )
    if body_content_types and body_content_types != {example_content_type}:
        report.error(
            "writing.example_content_type_mismatch",
            "完整正文案例必须与 writing_examples.content_type 一致",
            "writing_examples.content_type",
        )
    if viral_requested and "hook" not in loaded_assets:
        report.error(
            "writing.viral_hook_example_required",
            "用户明确要求病毒式传播时，完整正文案例之外还要读取开头案例",
            "writing_examples.references",
        )

    author_voice = _mapping(
        data.get("author_voice"),
        "author_voice",
        report,
    )
    _reject_unexpected_fields(
        author_voice,
        {"sources", "signals", "preserved_choices"},
        "author_voice",
        report,
    )
    voice_sources_value = author_voice.get("sources")
    if not isinstance(voice_sources_value, list) or not voice_sources_value:
        report.error(
            "writing.missing_author_voice_sources",
            "author_voice.sources 必须包含当前用户文字或经过确认的作者材料",
            "author_voice.sources",
        )
        voice_sources_value = []

    source_verifications: set[str] = set()
    user_voice_source_found = False
    for index, source_value in enumerate(voice_sources_value):
        field = f"author_voice.sources.{index}"
        source = _mapping(source_value, field, report)
        _reject_unexpected_fields(
            source,
            {"reference", "authorship", "verification"},
            field,
            report,
        )
        _required_text(source, "reference", report)
        authorship = _enum_value(
            source,
            "authorship",
            WRITING_SOURCE_AUTHORSHIPS,
            report,
        )
        verification = _enum_value(
            source,
            "verification",
            WRITING_SOURCE_VERIFICATIONS,
            report,
        )
        if authorship == "user":
            if verification not in USER_SOURCE_VERIFICATIONS:
                report.error(
                    "writing.unverified_author_voice",
                    "用户声音必须来自当前输入、确认稿或已发布内容",
                    field,
                )
            else:
                user_voice_source_found = True
        elif (
            authorship == "system_profile"
            and verification != "maintained_profile"
        ):
            report.error(
                "writing.invalid_voice_profile_provenance",
                "维护中的声音档案必须使用 maintained_profile 来源状态",
                field,
            )
        if verification:
            source_verifications.add(verification)

    if not user_voice_source_found:
        report.error(
            "writing.user_voice_source_required",
            "每次成文都要把当前用户文字或经过确认的作者原文交给生产者",
            "author_voice.sources",
        )

    voice_signals = _text_list(
        author_voice,
        "signals",
        report,
        required=True,
    )
    if len(voice_signals) > 5:
        report.error(
            "writing.too_many_voice_signals",
            "author_voice.signals 保留一至五项当前最有用的可观察声音信号",
            "author_voice.signals",
        )

    preserved_choices_value = author_voice.get("preserved_choices")
    if not isinstance(preserved_choices_value, list) or not all(
        isinstance(item, str) and item.strip()
        for item in preserved_choices_value
    ):
        report.error(
            "writing.invalid_preserved_choices",
            "author_voice.preserved_choices 必须是字符串数组，可为空",
            "author_voice.preserved_choices",
        )
        preserved_choices: set[str] = set()
    else:
        normalized_choices = [
            item.strip() for item in preserved_choices_value
        ]
        if len(normalized_choices) != len(set(normalized_choices)):
            report.error(
                "writing.duplicate_preserved_choice",
                "同一表达选择只记录一次",
                "author_voice.preserved_choices",
            )
        preserved_choices = set(normalized_choices)

    events_value = data.get("experience_events", [])
    if not isinstance(events_value, list):
        report.error(
            "writing.invalid_experience_events",
            "experience_events 必须是数组",
            "experience_events",
        )
        events_value = []
    event_stages: set[str] = set()
    for index, event_value in enumerate(events_value):
        field = f"experience_events.{index}"
        event = _mapping(event_value, field, report)
        _reject_unexpected_fields(
            event,
            {"stage", "detail", "source"},
            field,
            report,
        )
        stage = _enum_value(event, "stage", EXPERIENCE_STAGES, report)
        _required_text(event, "detail", report)
        event_source = _mapping(
            event.get("source"),
            f"{field}.source",
            report,
        )
        _reject_unexpected_fields(
            event_source,
            {"reference", "authorship", "verification"},
            f"{field}.source",
            report,
        )
        _required_text(event_source, "reference", report)
        event_authorship = _enum_value(
            event_source,
            "authorship",
            WRITING_SOURCE_AUTHORSHIPS,
            report,
        )
        event_verification = _enum_value(
            event_source,
            "verification",
            WRITING_SOURCE_VERIFICATIONS,
            report,
        )
        if (
            event_authorship != "user"
            or event_verification not in USER_SOURCE_VERIFICATIONS
        ):
            report.error(
                "writing.unverified_experience_source",
                "第一人称经历必须来自用户当前输入、确认稿或已发布文章",
                f"{field}.source",
            )
        if stage in event_stages:
            report.error(
                "writing.duplicate_experience_stage",
                f"经历节点重复：{stage}",
                f"{field}.stage",
            )
        if stage:
            event_stages.add(stage)

    if narrative_basis == "lived_chronology":
        if "trigger" not in event_stages:
            report.error(
                "writing.missing_experience_trigger",
                "经历型正文必须有来自用户材料的真实触发点",
                "experience_events",
            )
        if not event_stages.intersection({"attempt", "friction", "choice"}):
            report.error(
                "writing.missing_experience_process",
                "经历型正文必须有至少一个真实尝试、阻力或选择",
                "experience_events",
            )
        if not event_stages.intersection({"result", "judgment"}):
            report.error(
                "writing.missing_experience_outcome",
                "经历型正文必须说明材料中已有的当前结果或作者判断",
                "experience_events",
            )

    if deliverable == "github_project_short":
        _validate_github_project(data.get("github_project"), report)
        if example_content_type != "项目与产品介绍":
            report.error(
                "writing.github_example_type_required",
                "GitHub 项目短介绍使用“项目与产品介绍”完整案例",
                "writing_examples.content_type",
            )
    elif "github_project" in data:
        report.error(
            "writing.unexpected_github_project",
            "github_project 只用于 GitHub 项目短介绍",
            "github_project",
        )

    report.details.update(
        {
            "action": action,
            "deliverable": deliverable,
            "viral_requested": viral_requested,
            "narrative_basis": narrative_basis,
            "content_truth_count": content_truth_count,
            "content_truth_statuses": sorted(content_truth_statuses),
            "core_information_count": len(core_information),
            "requirement_count": len(requirements),
            "template_references": sorted(template_references),
            "example_reference_count": len(example_references),
            "example_assets": sorted(loaded_assets),
            "example_content_type": example_content_type,
            "author_voice_source_count": len(voice_sources_value),
            "author_voice_source_verifications": sorted(source_verifications),
            "voice_signal_count": len(voice_signals),
            "preserved_choice_count": len(preserved_choices),
            "experience_stages": sorted(event_stages),
            "distribution_portfolio_count": distribution_portfolio_count,
        }
    )
    return report


def validate_content_audit(data: dict[str, Any]) -> ValidationReport:
    """Validate a content-audit result before it is shown to the user."""

    report = ValidationReport()
    mode = _enum_value(data, "mode", AUDIT_MODES, report)
    threshold = _enum_value(
        data, "severity_threshold", AUDIT_SEVERITIES, report
    )
    scope = _enum_list(data, "scope", AUDIT_CATEGORIES, report)
    fact_check_requested = _bool_value(data, "fact_check_requested", report)
    external_research_started = _bool_value(
        data, "external_research_started", report
    )
    author_voice_protected = _bool_value(
        data, "author_voice_protected", report
    )

    if not author_voice_protected:
        report.error(
            "audit.voice_not_protected",
            "内容审计必须先保护作者已确认的声音和表达毛边",
            "author_voice_protected",
        )
    if external_research_started and not fact_check_requested:
        report.error(
            "audit.unrequested_external_research",
            "用户没有要求事实核查，内容审计不能开始外部研究",
            "external_research_started",
        )
    if mode == "content_only" and external_research_started:
        report.error(
            "audit.content_only_used_research",
            "content_only 模式只能使用用户提供的正文和材料",
            "mode",
        )
    if mode == "content_and_fact" and not fact_check_requested:
        report.error(
            "audit.fact_mode_without_request",
            "内容与事实审计必须由用户明确要求事实核查",
            "fact_check_requested",
        )
    if mode == "line_edit" and not scope.intersection({"language", "format"}):
        report.error(
            "audit.line_edit_without_language_scope",
            "逐字校对必须包含 language 或 format 范围",
            "scope",
        )

    findings_value = data.get("findings")
    if not isinstance(findings_value, list):
        report.error(
            "audit.invalid_findings",
            "findings 必须是数组；没有实质问题时使用空数组",
            "findings",
        )
        findings_value = []

    severity_counts = {severity: 0 for severity in AUDIT_SEVERITIES}
    seen_root_causes: set[str] = set()
    for index, finding_value in enumerate(findings_value):
        field = f"findings.{index}"
        finding = _mapping(finding_value, field, report)
        severity = _enum_value(
            finding, "severity", AUDIT_SEVERITIES, report
        )
        category = _enum_value(
            finding, "category", AUDIT_CATEGORIES, report
        )
        _required_text(finding, "issue", report)
        root_cause = _required_text(finding, "root_cause", report)
        _required_text(finding, "impact", report)
        _required_text(finding, "minimal_fix", report)
        _enum_value(finding, "action", AUDIT_ACTIONS, report)

        if severity:
            severity_counts[severity] += 1
            if (
                threshold
                and AUDIT_SEVERITY_LEVELS[severity]
                < AUDIT_SEVERITY_LEVELS[threshold]
            ):
                report.error(
                    "audit.finding_below_threshold",
                    "审计结果包含低于报告阈值的问题，应在交付前过滤",
                    f"{field}.severity",
                )
            if severity == "minor" and mode != "line_edit":
                report.error(
                    "audit.minor_finding_outside_line_edit",
                    "可容忍的小错误只在用户明确要求逐字校对时逐项报告",
                    f"{field}.severity",
                )
        if category and category not in scope:
            report.error(
                "audit.finding_outside_scope",
                "问题类别不在用户授权的审计范围内",
                f"{field}.category",
            )
        normalized_root_cause = _normalize_topic(root_cause)
        if normalized_root_cause:
            if normalized_root_cause in seen_root_causes:
                report.error(
                    "audit.duplicate_root_cause",
                    "同一根因不能拆成多个问题，应合并后只保留最有代表性的例子",
                    f"{field}.root_cause",
                )
            seen_root_causes.add(normalized_root_cause)

    report.details.update(
        {
            "mode": mode,
            "severity_threshold": threshold,
            "scope": sorted(scope),
            "finding_count": len(findings_value),
            "severity_counts": severity_counts,
        }
    )
    return report


def _declared_directories(home_path: Path) -> set[str]:
    directories: set[str] = set()
    for line in home_path.read_text(encoding="utf-8-sig").splitlines():
        match = HOME_DIRECTORY_RE.match(line)
        if match:
            directories.add(match.group(1).strip())
    return directories


def _normalize_topic(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _knowledge_filename_matches(kb_root: Path, names: list[str]) -> list[Path]:
    knowledge_root = kb_root / "10-Knowledge"
    if not knowledge_root.exists():
        return []
    normalized_names = {_normalize_topic(name) for name in names if _normalize_topic(name)}
    matches = []
    for candidate in knowledge_root.rglob("*.md"):
        candidate_terms = {
            _normalize_topic(term)
            for term in knowledge_note_terms(candidate)
            if _normalize_topic(term)
        }
        if candidate_terms & normalized_names:
            matches.append(candidate)
    return sorted(matches)


def _source_matches(kb_root: Path, identity: dict[str, str]) -> list[Path]:
    sources_root = kb_root / "20-Sources"
    if not sources_root.exists():
        return []
    title = identity.get("title", "").strip()
    url = identity.get("url", "").strip()
    content_hash = identity.get("hash", "").strip()
    normalized_title = _normalize_topic(title)
    matches: list[Path] = []

    for candidate in sources_root.rglob("*.md"):
        title_match = bool(normalized_title) and _normalize_topic(candidate.stem) == normalized_title
        content_match = False
        if url or content_hash:
            try:
                content = candidate.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                content = ""
            content_match = (bool(url) and url in content) or (
                bool(content_hash) and content_hash in content
            )
        if title_match or content_match:
            matches.append(candidate)
    return sorted(matches)


def validate_write_plan(
    data: dict[str, Any],
    repository_root: Path,
    *,
    knowledge_root: Path | None = None,
) -> ValidationReport:
    report = ValidationReport()
    repository_root = repository_root.resolve()
    if "kb_root" in data:
        report.error(
            "write.kb_root_override",
            "知识库固定为项目内的 System Knowledge，写入计划不能覆盖路径",
            "kb_root",
        )
    kb_root = (
        knowledge_root.resolve()
        if knowledge_root is not None
        else (repository_root / "System Knowledge").resolve()
    )
    home_path = kb_root / "Home.md"

    if not home_path.is_file():
        report.error("write.missing_home", "知识库缺少 Home.md，不能推测目录边界", "kb_root")
        return report
    if not _bool_value(data, "write_authorized", report):
        report.error("write.not_authorized", "没有写入授权，禁止执行写入计划", "write_authorized")

    topic = _required_text(data, "topic", report)
    aliases_value = data.get("aliases", [])
    if not isinstance(aliases_value, list) or not all(
        isinstance(alias, str) and alias.strip() for alias in aliases_value
    ):
        report.error("write.invalid_aliases", "aliases 必须是非空字符串数组", "aliases")
        aliases: list[str] = []
    else:
        aliases = [alias.strip() for alias in aliases_value]

    operations = data.get("operations")
    if not isinstance(operations, list) or not operations:
        report.error("write.missing_operations", "写入计划至少需要一个操作", "operations")
        operations = []

    declared_directories = _declared_directories(home_path)
    if not declared_directories:
        report.error("write.no_declared_directories", "Home.md 没有可解析的目录边界", "kb_root")

    names = [topic, *aliases] if topic else aliases
    knowledge_matches = _knowledge_filename_matches(kb_root, names)
    knowledge_match_set = {path.resolve() for path in knowledge_matches}
    seen_targets: set[Path] = set()
    source_matches_by_operation: dict[str, list[str]] = {}

    for index, operation_value in enumerate(operations):
        field = f"operations.{index}"
        operation = _mapping(operation_value, field, report)
        action = operation.get("action")
        if action not in WRITE_ACTIONS:
            report.error(
                "write.invalid_action",
                "只允许 create 或 update；删除、移动和兼容写入不属于本门禁",
                f"{field}.action",
            )
            continue
        path_value = operation.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            report.error("write.invalid_path", "path 必须是非空相对路径", f"{field}.path")
            continue
        relative_path = Path(path_value)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            report.error(
                "write.path_outside_kb",
                "写入目标必须是知识库内的相对路径",
                f"{field}.path",
            )
            continue
        target = (kb_root / relative_path).resolve()
        try:
            target.relative_to(kb_root)
        except ValueError:
            report.error(
                "write.path_outside_kb",
                "写入目标超出知识库边界",
                f"{field}.path",
            )
            continue
        if target in seen_targets:
            report.error("write.duplicate_operation", "同一路径出现重复操作", f"{field}.path")
        seen_targets.add(target)

        if not relative_path.parts or relative_path.parts[0] not in declared_directories:
            report.error(
                "write.undeclared_directory",
                "目标目录未在 Home.md 中声明",
                f"{field}.path",
            )
        if target.suffix.lower() != ".md":
            report.error("write.non_markdown_target", "当前只允许写入 Markdown 文件", f"{field}.path")
        if action == "create" and target.exists():
            report.error("write.create_existing", "create 目标已经存在，应改为 update", f"{field}.path")
        if action == "update" and not target.is_file():
            report.error("write.update_missing", "update 目标不存在", f"{field}.path")

        is_writing_output_target = (
            len(relative_path.parts) >= 2
            and relative_path.parts[0] == "40-Outputs"
            and relative_path.parts[1] == "Writing"
        )
        if is_writing_output_target:
            artifact = _mapping(
                operation.get("writing_artifact"),
                f"{field}.writing_artifact",
                report,
            )
            artifact_state = _enum_value(
                artifact,
                "state",
                WRITING_ARTIFACT_STATES,
                report,
            )
            artifact_source = _enum_value(
                artifact,
                "source",
                WRITING_ARTIFACT_SOURCES,
                report,
            )
            if artifact_state != "final" or artifact_source not in {
                "user-confirmed",
                "published-article",
            }:
                report.error(
                    "write.unverified_writing_output",
                    "40-Outputs/Writing 只接收用户确认稿或已发布文章；Agent 草稿和用户未确认草稿必须留在 30-Projects",
                    f"{field}.writing_artifact",
                )

        is_knowledge_target = bool(relative_path.parts) and relative_path.parts[0] == "10-Knowledge"
        if is_knowledge_target and action == "create" and knowledge_matches:
            report.error(
                "write.parallel_topic_source",
                "已经存在同主题或别名文件，不能创建平行主题文档",
                f"{field}.path",
            )
        if is_knowledge_target and action == "update" and len(knowledge_matches) > 1:
            report.error(
                "write.multiple_topic_sources",
                "活动知识目录中存在多个同名主题候选，必须先确定唯一真源",
                f"{field}.path",
            )
        if (
            is_knowledge_target
            and action == "update"
            and len(knowledge_matches) == 1
            and target not in knowledge_match_set
        ):
            report.error(
                "write.wrong_topic_target",
                "更新目标不是检索到的同主题唯一文件",
                f"{field}.path",
            )

        is_source_target = bool(relative_path.parts) and relative_path.parts[0] == "20-Sources"
        if is_source_target:
            identity_value = operation.get("source_identity")
            identity = _mapping(identity_value, f"{field}.source_identity", report)
            cleaned_identity: dict[str, str] = {}
            for key in ("title", "url", "hash"):
                value = identity.get(key, "")
                if value and not isinstance(value, str):
                    report.error(
                        "write.invalid_source_identity",
                        f"source_identity.{key} 必须是字符串",
                        f"{field}.source_identity.{key}",
                    )
                elif isinstance(value, str) and value.strip():
                    cleaned_identity[key] = value.strip()
            if not cleaned_identity:
                report.error(
                    "write.missing_source_identity",
                    "来源写入必须提供 title、url 或 hash 中至少一项用于查重",
                    f"{field}.source_identity",
                )
            else:
                source_matches = _source_matches(kb_root, cleaned_identity)
                source_match_set = {path.resolve() for path in source_matches}
                source_matches_by_operation[str(index)] = [
                    str(path.relative_to(kb_root)) for path in source_matches
                ]
                if action == "create" and source_matches:
                    report.error(
                        "write.duplicate_source",
                        "已经存在标题、URL 或哈希匹配的来源，不能创建平行来源文档",
                        f"{field}.path",
                    )
                if action == "update" and len(source_matches) > 1:
                    report.error(
                        "write.multiple_source_matches",
                        "存在多个来源候选，必须先确定唯一真源",
                        f"{field}.path",
                    )
                if action == "update" and len(source_matches) == 1 and target not in source_match_set:
                    report.error(
                        "write.wrong_source_target",
                        "更新目标不是查重得到的唯一来源文件",
                        f"{field}.path",
                    )

    report.details.update(
        {
            "kb_root": str(kb_root),
            "declared_directories": sorted(declared_directories),
            "knowledge_matches": [str(path.relative_to(kb_root)) for path in knowledge_matches],
            "source_matches_by_operation": source_matches_by_operation,
            "operation_count": len(operations),
        }
    )
    return report


def _valid_checked_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_evidence_bundle(data: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        report.error("evidence.missing_claims", "证据包至少需要一个主张", "claims")
        return report

    high_impact_count = 0
    quote_count = 0
    for claim_index, claim_value in enumerate(claims):
        field = f"claims.{claim_index}"
        claim = _mapping(claim_value, field, report)
        _reject_unexpected_fields(
            claim,
            {"claim", "impact", "is_quote", "time_sensitive", "sources"},
            field,
            report,
        )
        _required_text(claim, "claim", report)
        impact = claim.get("impact", "normal")
        if impact not in {"normal", "high"}:
            report.error("evidence.invalid_impact", "impact 必须是 normal 或 high", f"{field}.impact")
        is_quote = _bool_value(claim, "is_quote", report)
        time_sensitive = _bool_value(claim, "time_sensitive", report)

        sources_value = claim.get("sources", [])
        if not isinstance(sources_value, list):
            report.error("evidence.invalid_sources", "sources 必须是数组", f"{field}.sources")
            sources_value = []

        direct_verified: list[dict[str, Any]] = []
        high_quality: list[dict[str, Any]] = []
        timely: list[dict[str, Any]] = []
        for source_index, source_value in enumerate(sources_value):
            source_field = f"{field}.sources.{source_index}"
            source = _mapping(source_value, source_field, report)
            url = source.get("url")
            if not isinstance(url, str) or not url.strip():
                report.error("evidence.missing_url", "来源必须提供直接 URL", f"{source_field}.url")
                url = ""
            role = source.get("role")
            if role not in SOURCE_ROLES:
                report.error(
                    "evidence.invalid_role",
                    f"role 必须是以下值之一：{', '.join(sorted(SOURCE_ROLES))}",
                    f"{source_field}.role",
                )
            access = source.get("access")
            if access not in SOURCE_ACCESS:
                report.error(
                    "evidence.invalid_access",
                    f"access 必须是以下值之一：{', '.join(sorted(SOURCE_ACCESS))}",
                    f"{source_field}.access",
                )
            authority = source.get("authority", "unknown")
            if authority not in SOURCE_AUTHORITIES:
                report.error(
                    "evidence.invalid_authority",
                    f"authority 必须是以下值之一：{', '.join(sorted(SOURCE_AUTHORITIES))}",
                    f"{source_field}.authority",
                )
            verified = _bool_value(source, "verified", report)

            if access == "direct" and verified and url:
                direct_verified.append(source)
                if authority in HIGH_IMPACT_AUTHORITIES:
                    high_quality.append(source)
                if _valid_checked_date(source.get("checked_at")):
                    timely.append(source)

        if not sources_value:
            report.warning("evidence.unsourced_claim", "主张没有来源", field)
        if is_quote:
            quote_count += 1
            if not direct_verified:
                report.error(
                    "evidence.quote_without_original",
                    "精确引用必须有已核对的直接原文链接",
                    field,
                )
        if impact == "high":
            high_impact_count += 1
            if not high_quality:
                report.error(
                    "evidence.high_impact_without_primary",
                    "高影响主张必须有已核对的官方或原始来源",
                    field,
                )
        if time_sensitive and not timely:
            report.error(
                "evidence.time_sensitive_without_date",
                "实时主张必须记录直接来源的核查日期 checked_at",
                field,
            )

    report.details.update(
        {
            "claim_count": len(claims),
            "high_impact_count": high_impact_count,
            "quote_count": quote_count,
        }
    )
    return report
