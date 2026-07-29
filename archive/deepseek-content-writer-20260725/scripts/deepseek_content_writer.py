"""已归档的 DeepSeek 写作入口，不参与当前运行。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-pro"
DEFAULT_ENV_FILE = Path(r"D:\Tools\100x-learning\deepseek.env")
DEFAULT_MAX_TOKENS = 32_768
DEFAULT_TIMEOUT_SECONDS = 600

SYSTEM_PROMPT = """你负责把已经整理和核验的内容包写成用户要求的独立短内容、GitHub 项目短介绍、平台内容组合、文章或 Newsletter。

subject 是唯一写作对象。core_message 按顺序定义读者最终必须记住的信息，先让它们清楚成立，再用 content_truth 中的事实、经历、例子、引语和来源支撑。audience、deliverable、creative_direction 和 hard_constraints 共同定义本次成品。

内容包包含 editorial_position 时，它定义作者已经确认的观点取向、信息取舍和主张边界，决定这次内容强调什么、如何评价以及说到哪里。内容包包含 voice_contract 时，它只决定视角、推进、段落、素材角色、幽默、结尾和稳定表达习惯。voice_contract 不能改变 editorial_position、core_message 或 content_truth；editorial_position 也不能代替具体表达。creative_direction 负责本次成品的注意力任务、阅读感受、信息密度和传播张力。

content_mode=general 时，直接按通用写作合同成文。

content_mode=github_project_short 时，写成普通读者能够独立理解的简短项目介绍。先用独立措辞的开头完成 creative_direction 指定的注意力任务，再说明谁使用这个项目做什么、最后得到什么；正文只选择 core_message 需要的高价值能力，并按 deliverable 与 hard_constraints 决定篇幅、emoji、项目关系、链接和结尾。正文形态服从信息关系：并列能力需要快速扫描时可以使用列表，背景、因果、过程或项目关系需要连续解释时使用短段落，两类信息同时存在时可以混合组织。每个功能句只组合 content_truth 中已经提供的动作、条件和直接结果；额外的省时、省力、质量、控制权或使用范围判断也必须由 content_truth 支持。content_truth 提供带核对日期的当前 GitHub star 数量时，将它自然写入正文，并固定使用 star 这个词。风格样稿决定语气、节奏、信息顺序和版式，当前项目的具体句子重新创作。content_truth 中标记为项目方声明的信息保留来源身份，时间性表述使用其中带日期的来源，本次观察只写已经真实发生的结果。项目链接与开源信息组成一个收束段；hard_constraints 要求逐字结尾且链接无法放入该句时，链接紧邻其前，并且开源事实只陈述一次。

content_mode=social_distribution 时，distribution_plan 是平台、读者状态、内容原子、帖子任务、开头策略、互动、CTA、平台规则和热点使用的唯一分发计划；完整生成 portfolio 中的全部条目，让每条内容能够独立成立，并且只使用 content_truth 和计划引用的内容原子。计划中的 missing 链接要在成品中明确标记，不得补写地址。内部计划字段不进入正文，除非 deliverable 明确要求展示。

在 content_truth 范围内充分发挥传播技巧，以注意、清晰、记忆和传播效果为目标，自由选择合适的修辞、节奏、结构和篇幅。可核验信息、经历、引语、承诺和行动依据由 content_truth 提供；信息缺口在对应位置使用最小待补充标记。新写文字不得使用“不是 A，而是 B”及其添加连接词、替换标点或拆行后的变体；需要比较或纠正误解时，先直接陈述成立的主张，再单独说明另一种认识造成的影响。

返回值直接从成品文字开始，以最后一句成品文字结束。"""

PACKET_FIELDS = {
    "action",
    "content_mode",
    "subject",
    "core_message",
    "content_truth",
    "audience",
    "deliverable",
    "editorial_position",
    "voice_contract",
    "creative_direction",
    "hard_constraints",
    "distribution_plan",
    "current_text",
    "revision_request",
}
ACTIONS = {"draft", "revise"}
CONTENT_MODES = {"general", "github_project_short", "social_distribution"}
ATOM_TYPES = {
    "claim",
    "data",
    "insight",
    "framework",
    "story",
    "proof",
    "quote",
    "objection",
    "resource",
}
CTA_MODES = {"none", "body", "first_comment_or_reply"}
CTA_DESTINATION_STATUSES = {"not_needed", "provided", "source_url", "missing"}
PLATFORM_CHECK_STATUSES = {"verified", "not_required", "unavailable"}
TREND_STATUSES = {"not_requested", "not_used", "used", "unavailable"}
FORBIDDEN_CONTRAST_RE = re.compile(
    r"不(?:是|等于)[^。！？\n]{1,80}"
    r"(?:[，,；;：:\n]|[。！？]\s*)\s*"
    r"(?:而是|却是|只是|真正(?:的|要|该)?是|"
    r"(?:答案|重点|关键|原因|问题|缺口|目标|做法)?\s*是|等于)"
    r"[^。！？\n]{1,80}"
)

READER_FIELDS = {
    "role",
    "context",
    "job",
    "pain",
    "desired_outcome",
    "awareness",
    "objection",
}
ATOM_FIELDS = {"id", "type", "content", "source_boundary"}
CTA_FIELDS = {"mode", "promise", "destination_status", "destination"}
PORTFOLIO_FIELDS = {
    "id",
    "platform",
    "format",
    "job",
    "angle",
    "atom_ids",
    "hook_strategy",
    "value_delivery",
    "engagement",
    "cta",
}
PLATFORM_CHECK_FIELDS = {
    "platform",
    "status",
    "checked_at",
    "sources",
    "constraints",
}
TREND_FIELDS = {"status", "bridge", "sources"}
EDITORIAL_POSITION_FIELDS = {
    "source",
    "position",
    "selection_rules",
    "claim_boundaries",
}
VOICE_CONTRACT_TEXT_FIELDS = {
    "narrative_driver",
    "point_of_view",
    "opening",
    "layout",
    "media_role",
    "humor_mechanism",
    "ending",
}
VOICE_CONTRACT_REQUIRED_LIST_FIELDS = {"avoid", "stable_traits"}
VOICE_CONTRACT_OPTIONAL_LIST_FIELDS = {"sample_specific_traits"}
VOICE_CONTRACT_FIELDS = (
    VOICE_CONTRACT_TEXT_FIELDS
    | VOICE_CONTRACT_REQUIRED_LIST_FIELDS
    | VOICE_CONTRACT_OPTIONAL_LIST_FIELDS
)
DISTRIBUTION_PLAN_FIELDS = {
    "primary_reader",
    "reader_action",
    "content_atoms",
    "portfolio",
    "platform_checks",
    "trend",
}


class WriterError(RuntimeError):
    pass


def _required_text(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise WriterError(f"{field} 必须是非空字符串")
    return value.strip()


def _string_list(data: dict[str, Any], field: str, *, allow_empty: bool) -> list[str]:
    value = data.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise WriterError(f"{field} 必须是字符串数组")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise WriterError(f"{field} 不能为空")
    return result


def _exact_object(value: Any, field: str, required_fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WriterError(f"{field} 必须是对象")
    unknown = sorted(set(value) - required_fields)
    if unknown:
        raise WriterError(f"{field} 包含未知字段：{', '.join(unknown)}")
    missing = sorted(required_fields - set(value))
    if missing:
        raise WriterError(f"{field} 缺少字段：{', '.join(missing)}")
    return value


def _nested_text(
    data: dict[str, Any],
    name: str,
    parent: str,
    *,
    allow_empty: bool = False,
) -> str:
    value = data.get(name)
    if not isinstance(value, str):
        raise WriterError(f"{parent}.{name} 必须是字符串")
    result = value.strip()
    if not allow_empty and not result:
        raise WriterError(f"{parent}.{name} 不能为空")
    return result


def _nested_enum(
    data: dict[str, Any],
    name: str,
    parent: str,
    allowed: set[str],
) -> str:
    value = _nested_text(data, name, parent)
    if value not in allowed:
        raise WriterError(
            f"{parent}.{name} 只允许：{', '.join(sorted(allowed))}"
        )
    return value


def validate_editorial_position(value: Any) -> dict[str, Any]:
    position = _exact_object(
        value, "editorial_position", EDITORIAL_POSITION_FIELDS
    )
    return {
        "source": _required_text(position, "source"),
        "position": _required_text(position, "position"),
        "selection_rules": _string_list(
            position, "selection_rules", allow_empty=False
        ),
        "claim_boundaries": _string_list(
            position, "claim_boundaries", allow_empty=True
        ),
    }


def validate_voice_contract(value: Any) -> dict[str, Any]:
    contract = _exact_object(value, "voice_contract", VOICE_CONTRACT_FIELDS)
    validated: dict[str, Any] = {
        field: _required_text(contract, field)
        for field in sorted(VOICE_CONTRACT_TEXT_FIELDS)
    }
    for field in sorted(VOICE_CONTRACT_REQUIRED_LIST_FIELDS):
        validated[field] = _string_list(contract, field, allow_empty=False)
    for field in sorted(VOICE_CONTRACT_OPTIONAL_LIST_FIELDS):
        validated[field] = _string_list(contract, field, allow_empty=True)

    overlap = set(validated["stable_traits"]).intersection(
        validated["sample_specific_traits"]
    )
    if overlap:
        raise WriterError(
            "voice_contract 的 stable_traits 与 sample_specific_traits "
            f"不能重复：{', '.join(sorted(overlap))}"
        )
    return validated


def _nested_string_list(
    data: dict[str, Any],
    name: str,
    parent: str,
    *,
    allow_empty: bool,
) -> list[str]:
    value = data.get(name)
    field = f"{parent}.{name}"
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise WriterError(f"{field} 必须是非空字符串组成的数组")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise WriterError(f"{field} 不能为空")
    if len(result) != len(set(result)):
        raise WriterError(f"{field} 不能包含重复项")
    return result


def validate_distribution_plan(value: Any) -> dict[str, Any]:
    plan = _exact_object(value, "distribution_plan", DISTRIBUTION_PLAN_FIELDS)

    reader_value = _exact_object(
        plan.get("primary_reader"),
        "distribution_plan.primary_reader",
        READER_FIELDS,
    )
    reader_parent = "distribution_plan.primary_reader"
    primary_reader = {
        "role": _nested_text(reader_value, "role", reader_parent),
        "context": _nested_text(reader_value, "context", reader_parent),
        "job": _nested_text(reader_value, "job", reader_parent),
        "pain": _nested_text(reader_value, "pain", reader_parent),
        "desired_outcome": _nested_text(
            reader_value, "desired_outcome", reader_parent
        ),
        "awareness": _nested_text(reader_value, "awareness", reader_parent),
        "objection": _nested_text(
            reader_value, "objection", reader_parent, allow_empty=True
        ),
    }
    reader_action = _nested_text(plan, "reader_action", "distribution_plan")

    atom_values = plan.get("content_atoms")
    if not isinstance(atom_values, list) or not atom_values:
        raise WriterError("distribution_plan.content_atoms 必须是非空数组")
    content_atoms: list[dict[str, Any]] = []
    atom_ids: set[str] = set()
    for index, atom_value in enumerate(atom_values):
        parent = f"distribution_plan.content_atoms.{index}"
        atom = _exact_object(atom_value, parent, ATOM_FIELDS)
        atom_id = _nested_text(atom, "id", parent)
        if atom_id in atom_ids:
            raise WriterError(f"distribution_plan.content_atoms 出现重复 id：{atom_id}")
        atom_ids.add(atom_id)
        content_atoms.append(
            {
                "id": atom_id,
                "type": _nested_enum(atom, "type", parent, ATOM_TYPES),
                "content": _nested_text(atom, "content", parent),
                "source_boundary": _nested_text(
                    atom, "source_boundary", parent
                ),
            }
        )

    portfolio_values = plan.get("portfolio")
    if not isinstance(portfolio_values, list) or not portfolio_values:
        raise WriterError("distribution_plan.portfolio 必须是非空数组")
    portfolio: list[dict[str, Any]] = []
    portfolio_ids: set[str] = set()
    portfolio_platforms: set[str] = set()
    for index, post_value in enumerate(portfolio_values):
        parent = f"distribution_plan.portfolio.{index}"
        post = _exact_object(post_value, parent, PORTFOLIO_FIELDS)
        post_id = _nested_text(post, "id", parent)
        if post_id in portfolio_ids:
            raise WriterError(f"distribution_plan.portfolio 出现重复 id：{post_id}")
        portfolio_ids.add(post_id)
        platform = _nested_text(post, "platform", parent)
        portfolio_platforms.add(platform)
        selected_atom_ids = _nested_string_list(
            post, "atom_ids", parent, allow_empty=False
        )
        missing_atom_ids = sorted(set(selected_atom_ids) - atom_ids)
        if missing_atom_ids:
            raise WriterError(
                f"{parent}.atom_ids 引用了不存在的内容原子："
                f"{', '.join(missing_atom_ids)}"
            )

        cta_parent = f"{parent}.cta"
        cta_value = _exact_object(post.get("cta"), cta_parent, CTA_FIELDS)
        cta_mode = _nested_enum(cta_value, "mode", cta_parent, CTA_MODES)
        promise = _nested_text(
            cta_value, "promise", cta_parent, allow_empty=True
        )
        destination_status = _nested_enum(
            cta_value,
            "destination_status",
            cta_parent,
            CTA_DESTINATION_STATUSES,
        )
        destination = _nested_text(
            cta_value, "destination", cta_parent, allow_empty=True
        )
        if cta_mode == "none":
            if destination_status != "not_needed" or promise or destination:
                raise WriterError(
                    f"{cta_parent} 在 mode=none 时必须使用 not_needed，"
                    "promise 和 destination 保持空字符串"
                )
        else:
            if not promise:
                raise WriterError(f"{cta_parent}.promise 在启用 CTA 时不能为空")
            if destination_status == "not_needed":
                raise WriterError(
                    f"{cta_parent}.destination_status 在启用 CTA 时不能使用 not_needed"
                )
            if destination_status in {"provided", "source_url"} and not destination:
                raise WriterError(
                    f"{cta_parent}.destination 在已有入口时不能为空"
                )
            if destination_status == "missing" and destination:
                raise WriterError(
                    f"{cta_parent}.destination 在状态为 missing 时必须为空字符串"
                )

        portfolio.append(
            {
                "id": post_id,
                "platform": platform,
                "format": _nested_text(post, "format", parent),
                "job": _nested_text(post, "job", parent),
                "angle": _nested_text(post, "angle", parent),
                "atom_ids": selected_atom_ids,
                "hook_strategy": _nested_text(post, "hook_strategy", parent),
                "value_delivery": _nested_text(post, "value_delivery", parent),
                "engagement": _nested_text(post, "engagement", parent),
                "cta": {
                    "mode": cta_mode,
                    "promise": promise,
                    "destination_status": destination_status,
                    "destination": destination,
                },
            }
        )

    check_values = plan.get("platform_checks")
    if not isinstance(check_values, list) or not check_values:
        raise WriterError("distribution_plan.platform_checks 必须是非空数组")
    platform_checks: list[dict[str, Any]] = []
    checked_platforms: set[str] = set()
    for index, check_value in enumerate(check_values):
        parent = f"distribution_plan.platform_checks.{index}"
        check = _exact_object(check_value, parent, PLATFORM_CHECK_FIELDS)
        platform = _nested_text(check, "platform", parent)
        if platform in checked_platforms:
            raise WriterError(
                f"distribution_plan.platform_checks 出现重复平台：{platform}"
            )
        checked_platforms.add(platform)
        status = _nested_enum(
            check, "status", parent, PLATFORM_CHECK_STATUSES
        )
        checked_at = _nested_text(
            check, "checked_at", parent, allow_empty=True
        )
        sources = _nested_string_list(
            check, "sources", parent, allow_empty=True
        )
        constraints = _nested_string_list(
            check, "constraints", parent, allow_empty=True
        )
        if checked_at:
            try:
                date.fromisoformat(checked_at)
            except ValueError as exc:
                raise WriterError(
                    f"{parent}.checked_at 必须是 YYYY-MM-DD 日期"
                ) from exc
        if status == "verified" and (
            not checked_at or not sources or not constraints
        ):
            raise WriterError(
                f"{parent} 在 status=verified 时必须提供核查日期、来源和有效约束"
            )
        platform_checks.append(
            {
                "platform": platform,
                "status": status,
                "checked_at": checked_at,
                "sources": sources,
                "constraints": constraints,
            }
        )

    missing_checks = sorted(portfolio_platforms - checked_platforms)
    if missing_checks:
        raise WriterError(
            "distribution_plan.platform_checks 缺少 portfolio 平台："
            + ", ".join(missing_checks)
        )

    trend_parent = "distribution_plan.trend"
    trend_value = _exact_object(plan.get("trend"), trend_parent, TREND_FIELDS)
    trend_status = _nested_enum(
        trend_value, "status", trend_parent, TREND_STATUSES
    )
    trend_bridge = _nested_text(
        trend_value, "bridge", trend_parent, allow_empty=True
    )
    trend_sources = _nested_string_list(
        trend_value, "sources", trend_parent, allow_empty=True
    )
    if trend_status == "used" and (not trend_bridge or not trend_sources):
        raise WriterError(
            "distribution_plan.trend 在 status=used 时必须提供 bridge 和 sources"
        )
    if trend_status == "not_requested" and (trend_bridge or trend_sources):
        raise WriterError(
            "distribution_plan.trend 在 status=not_requested 时必须保持 bridge 和 sources 为空"
        )

    return {
        "primary_reader": primary_reader,
        "reader_action": reader_action,
        "content_atoms": content_atoms,
        "portfolio": portfolio,
        "platform_checks": platform_checks,
        "trend": {
            "status": trend_status,
            "bridge": trend_bridge,
            "sources": trend_sources,
        },
    }


def validate_packet(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WriterError("内容包顶层必须是 JSON 对象")

    unknown = sorted(set(value) - PACKET_FIELDS)
    if unknown:
        raise WriterError(f"内容包包含未知字段：{', '.join(unknown)}")

    action = _required_text(value, "action")
    if action not in ACTIONS:
        raise WriterError("action 只允许 draft 或 revise")

    content_mode = _required_text(value, "content_mode")
    if content_mode not in CONTENT_MODES:
        raise WriterError(
            "content_mode 只允许 general、github_project_short 或 "
            "social_distribution"
        )

    packet: dict[str, Any] = {
        "action": action,
        "content_mode": content_mode,
        "subject": _required_text(value, "subject"),
        "core_message": _string_list(value, "core_message", allow_empty=False),
        "content_truth": _required_text(value, "content_truth"),
        "audience": _required_text(value, "audience"),
        "deliverable": _required_text(value, "deliverable"),
        "creative_direction": _required_text(value, "creative_direction"),
    }

    if "editorial_position" in value:
        packet["editorial_position"] = validate_editorial_position(
            value["editorial_position"]
        )
    if "voice_contract" in value:
        packet["voice_contract"] = validate_voice_contract(
            value["voice_contract"]
        )

    packet["hard_constraints"] = _string_list(
        value, "hard_constraints", allow_empty=True
    )

    if content_mode == "social_distribution":
        if "distribution_plan" not in value:
            raise WriterError(
                "content_mode=social_distribution 必须包含 distribution_plan"
            )
        packet["distribution_plan"] = validate_distribution_plan(
            value["distribution_plan"]
        )
    elif "distribution_plan" in value:
        raise WriterError(
            f"content_mode={content_mode} 的内容包不能包含 distribution_plan"
        )

    if action == "revise":
        packet["current_text"] = _required_text(value, "current_text")
        packet["revision_request"] = _required_text(value, "revision_request")
    elif "current_text" in value or "revision_request" in value:
        raise WriterError("draft 内容包不能包含 current_text 或 revision_request")

    return packet


def build_payload(packet: dict[str, Any], max_tokens: int) -> dict[str, Any]:
    if max_tokens <= 0:
        raise WriterError("max_tokens 必须大于 0")
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(packet, ensure_ascii=False, indent=2),
            },
        ],
        "max_tokens": max_tokens,
        "stream": False,
    }


def parse_env_file(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise WriterError(f"无法读取本地配置：{path}") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise WriterError(f"本地配置第 {line_number} 行缺少等号：{path}")
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[name] = value
    return values


def resolve_env_file(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    configured = os.environ.get("DEEPSEEK_ENV_FILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_ENV_FILE


def resolve_api_key(env_file: Path) -> str:
    environment_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if environment_key:
        return environment_key
    values = parse_env_file(env_file)
    api_key = values.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise WriterError(f"本地配置缺少 DEEPSEEK_API_KEY：{env_file}")
    return api_key


def _request_json(
    *,
    method: str,
    path: str,
    api_key: str,
    timeout: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if timeout <= 0:
        raise WriterError("timeout 必须大于 0")
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{BASE_URL}/{path.lstrip('/')}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise WriterError(
            f"DeepSeek API 返回 HTTP {exc.code}：{response_body[:1000]}"
        ) from exc
    except URLError as exc:
        raise WriterError(f"无法连接 DeepSeek API：{exc.reason}") from exc

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WriterError("DeepSeek API 返回了无效 JSON") from exc
    if not isinstance(value, dict):
        raise WriterError("DeepSeek API 返回的顶层数据不是对象")
    return value


def available_models(api_key: str, timeout: int) -> list[str]:
    response = _request_json(
        method="GET",
        path="models",
        api_key=api_key,
        timeout=timeout,
    )
    items = response.get("data")
    if not isinstance(items, list):
        raise WriterError("DeepSeek models 响应缺少 data 数组")
    models = sorted(
        item["id"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )
    if MODEL not in models:
        raise WriterError(f"当前账户不可用模型列表中没有 {MODEL}")
    return models


def generate_content(
    packet: dict[str, Any],
    *,
    api_key: str,
    max_tokens: int,
    timeout: int,
) -> tuple[str, dict[str, Any]]:
    response = _request_json(
        method="POST",
        path="chat/completions",
        api_key=api_key,
        timeout=timeout,
        payload=build_payload(packet, max_tokens),
    )
    response_model = response.get("model")
    if response_model != MODEL:
        raise WriterError(
            f"DeepSeek 返回模型与请求不一致：expected={MODEL!r}, actual={response_model!r}"
        )
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise WriterError("DeepSeek 响应缺少 choices")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise WriterError("DeepSeek choices[0] 不是对象")
    finish_reason = choice.get("finish_reason")
    if finish_reason != "stop":
        raise WriterError(f"DeepSeek 未完整生成内容，finish_reason={finish_reason!r}")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise WriterError("DeepSeek 响应缺少 message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise WriterError("DeepSeek 响应没有可交付正文")

    usage = response.get("usage")
    metadata = {
        "provider": "DeepSeek",
        "model": response_model,
        "finish_reason": finish_reason,
        "usage": usage if isinstance(usage, dict) else {},
    }
    return content.strip(), metadata


def _match_is_verified_quote(
    content: str,
    match: re.Match[str],
    packet: dict[str, Any] | None,
) -> bool:
    if packet is None:
        return False
    matched_text = match.group(0).strip()
    content_truth = packet.get("content_truth", "")
    if not isinstance(content_truth, str) or matched_text not in content_truth:
        return False

    line_start = content.rfind("\n", 0, match.start()) + 1
    line_end = content.find("\n", match.end())
    if line_end == -1:
        line_end = len(content)
    line = content[line_start:line_end]
    if line.lstrip().startswith(">"):
        return True

    relative_start = match.start() - line_start
    relative_end = match.end() - line_start
    before = line[:relative_start]
    through_and_after = line[relative_start:]
    quote_pairs = (("“", "”"), ('"', '"'), ("「", "」"), ("『", "』"))
    for opening, closing in quote_pairs:
        opening_index = before.rfind(opening)
        if opening_index == -1:
            continue
        closing_index = through_and_after.find(closing)
        if closing_index != -1 and relative_start + closing_index >= relative_end - 1:
            return True
    return False


def content_quality_issues(
    content: str,
    packet: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    for match in FORBIDDEN_CONTRAST_RE.finditer(content):
        if not _match_is_verified_quote(content, match, packet):
            issues.append("正文使用了禁用的预制二元对照句式")
            break
    return issues


def build_quality_revision_packet(
    packet: dict[str, Any],
    current_text: str,
    issues: list[str],
) -> dict[str, Any]:
    revision = dict(packet)
    revision.update(
        {
            "action": "revise",
            "current_text": current_text,
            "revision_request": (
                "修正以下交付门禁问题："
                + "；".join(issues)
                + "。完整返回修订后的成品，保持原有 subject、core_message、"
                "content_truth、editorial_position、voice_contract、deliverable "
                "和 distribution_plan。每个比较先直接"
                "陈述成立的判断，再用独立句子说明另一种认识的影响。"
            ),
        }
    )
    return validate_packet(revision)


def generate_deliverable(
    packet: dict[str, Any],
    *,
    api_key: str,
    max_tokens: int,
    timeout: int,
) -> tuple[str, dict[str, Any]]:
    content, metadata = generate_content(
        packet,
        api_key=api_key,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    issues = content_quality_issues(content, packet)
    if not issues:
        result_metadata = dict(metadata)
        result_metadata["quality_gate"] = {"attempts": 1, "repairs": []}
        return content, result_metadata

    revision_packet = build_quality_revision_packet(packet, content, issues)
    revised_content, revised_metadata = generate_content(
        revision_packet,
        api_key=api_key,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    remaining_issues = content_quality_issues(revised_content, revision_packet)
    if remaining_issues:
        raise WriterError(
            "DeepSeek 修订后仍未通过正文门禁：" + "；".join(remaining_issues)
        )

    result_metadata = dict(revised_metadata)
    result_metadata["quality_gate"] = {
        "attempts": 2,
        "repairs": issues,
        "initial_usage": metadata.get("usage", {}),
    }
    return revised_content, result_metadata


def _load_packet(source: str) -> dict[str, Any]:
    try:
        if source == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(source).read_text(encoding="utf-8-sig")
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WriterError(f"无法读取内容包：{exc}") from exc
    return validate_packet(value)


def _write_content(content: str, output: str | None) -> None:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content + "\n", encoding="utf-8")
        return
    sys.stdout.write(content)
    if not content.endswith("\n"):
        sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Use DeepSeek V4 Pro as the content-writing producer"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="verify credentials and model access")
    check.add_argument("--env-file", help="local env file containing DEEPSEEK_API_KEY")
    check.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)

    write = subparsers.add_parser("write", help="generate or revise a content artifact")
    write.add_argument("--input", required=True, help="content-packet JSON path, or -")
    write.add_argument("--output", help="write final content to this path")
    write.add_argument("--env-file", help="local env file containing DEEPSEEK_API_KEY")
    write.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    write.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        env_file = resolve_env_file(args.env_file)
        api_key = resolve_api_key(env_file)
        if args.command == "check":
            models = available_models(api_key, args.timeout)
            json.dump(
                {"ok": True, "required_model": MODEL, "available_models": models},
                sys.stdout,
                ensure_ascii=False,
                indent=2,
            )
            sys.stdout.write("\n")
            return 0

        packet = _load_packet(args.input)
        content, metadata = generate_deliverable(
            packet,
            api_key=api_key,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
        _write_content(content, args.output)
        json.dump(metadata, sys.stderr, ensure_ascii=False)
        sys.stderr.write("\n")
        return 0
    except WriterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
