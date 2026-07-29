from __future__ import annotations

from datetime import date
from typing import Any


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
DISTRIBUTION_PLAN_FIELDS = {
    "primary_reader",
    "reader_action",
    "content_atoms",
    "portfolio",
    "platform_checks",
    "trend",
}


class DistributionPlanError(ValueError):
    pass


def _exact_object(value: Any, field: str, required_fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DistributionPlanError(f"{field} 必须是对象")
    unknown = sorted(set(value) - required_fields)
    if unknown:
        raise DistributionPlanError(f"{field} 包含未知字段：{', '.join(unknown)}")
    missing = sorted(required_fields - set(value))
    if missing:
        raise DistributionPlanError(f"{field} 缺少字段：{', '.join(missing)}")
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
        raise DistributionPlanError(f"{parent}.{name} 必须是字符串")
    result = value.strip()
    if not allow_empty and not result:
        raise DistributionPlanError(f"{parent}.{name} 不能为空")
    return result


def _nested_enum(
    data: dict[str, Any],
    name: str,
    parent: str,
    allowed: set[str],
) -> str:
    value = _nested_text(data, name, parent)
    if value not in allowed:
        raise DistributionPlanError(
            f"{parent}.{name} 只允许：{', '.join(sorted(allowed))}"
        )
    return value


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
        raise DistributionPlanError(f"{field} 必须是非空字符串组成的数组")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise DistributionPlanError(f"{field} 不能为空")
    if len(result) != len(set(result)):
        raise DistributionPlanError(f"{field} 不能包含重复项")
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
        raise DistributionPlanError("distribution_plan.content_atoms 必须是非空数组")
    content_atoms: list[dict[str, Any]] = []
    atom_ids: set[str] = set()
    for index, atom_value in enumerate(atom_values):
        parent = f"distribution_plan.content_atoms.{index}"
        atom = _exact_object(atom_value, parent, ATOM_FIELDS)
        atom_id = _nested_text(atom, "id", parent)
        if atom_id in atom_ids:
            raise DistributionPlanError(
                f"distribution_plan.content_atoms 出现重复 id：{atom_id}"
            )
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
        raise DistributionPlanError("distribution_plan.portfolio 必须是非空数组")
    portfolio: list[dict[str, Any]] = []
    portfolio_ids: set[str] = set()
    portfolio_platforms: set[str] = set()
    for index, post_value in enumerate(portfolio_values):
        parent = f"distribution_plan.portfolio.{index}"
        post = _exact_object(post_value, parent, PORTFOLIO_FIELDS)
        post_id = _nested_text(post, "id", parent)
        if post_id in portfolio_ids:
            raise DistributionPlanError(
                f"distribution_plan.portfolio 出现重复 id：{post_id}"
            )
        portfolio_ids.add(post_id)
        platform = _nested_text(post, "platform", parent)
        portfolio_platforms.add(platform)
        selected_atom_ids = _nested_string_list(
            post, "atom_ids", parent, allow_empty=False
        )
        missing_atom_ids = sorted(set(selected_atom_ids) - atom_ids)
        if missing_atom_ids:
            raise DistributionPlanError(
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
                raise DistributionPlanError(
                    f"{cta_parent} 在 mode=none 时必须使用 not_needed，"
                    "promise 和 destination 保持空字符串"
                )
        else:
            if not promise:
                raise DistributionPlanError(
                    f"{cta_parent}.promise 在启用 CTA 时不能为空"
                )
            if destination_status == "not_needed":
                raise DistributionPlanError(
                    f"{cta_parent}.destination_status 在启用 CTA 时不能使用 not_needed"
                )
            if destination_status in {"provided", "source_url"} and not destination:
                raise DistributionPlanError(
                    f"{cta_parent}.destination 在已有入口时不能为空"
                )
            if destination_status == "missing" and destination:
                raise DistributionPlanError(
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
        raise DistributionPlanError(
            "distribution_plan.platform_checks 必须是非空数组"
        )
    platform_checks: list[dict[str, Any]] = []
    checked_platforms: set[str] = set()
    for index, check_value in enumerate(check_values):
        parent = f"distribution_plan.platform_checks.{index}"
        check = _exact_object(check_value, parent, PLATFORM_CHECK_FIELDS)
        platform = _nested_text(check, "platform", parent)
        if platform in checked_platforms:
            raise DistributionPlanError(
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
                raise DistributionPlanError(
                    f"{parent}.checked_at 必须是 YYYY-MM-DD 日期"
                ) from exc
        if status == "verified" and (
            not checked_at or not sources or not constraints
        ):
            raise DistributionPlanError(
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
        raise DistributionPlanError(
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
        raise DistributionPlanError(
            "distribution_plan.trend 在 status=used 时必须提供 bridge 和 sources"
        )
    if trend_status == "not_requested" and (trend_bridge or trend_sources):
        raise DistributionPlanError(
            "distribution_plan.trend 在 status=not_requested 时必须保持 "
            "bridge 和 sources 为空"
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
