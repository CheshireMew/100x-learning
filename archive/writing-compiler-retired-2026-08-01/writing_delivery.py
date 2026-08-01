from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.content_case_library import build_search_receipt, search_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEARCH_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "content-case-search.schema.json"
RECORD_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "writing-execution-record.schema.json"
SUPPORTED_SCHEMA_VERSION = 1
SOURCE_KINDS = {
    "current_material": "当前材料",
    "project_self_description": "项目自述",
    "verified_primary": "本轮核验的一手来源",
    "observation": "真实观察",
    "third_party": "第三方反馈",
}
IMPROVEMENT_LABELS = {
    "clarity": "清楚程度",
    "density": "信息密度",
    "rhythm": "节奏",
    "reader_reaction": "目标读者反应",
}


class DeliveryError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryError(f"无法读取 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DeliveryError(f"JSON 根节点必须是对象：{path}")
    return value


def _resolve_local_ref(root: Mapping[str, Any], ref: str) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise DeliveryError(f"只支持 schema 内部引用：{ref}")
    value: Any = root
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or key not in value:
            raise DeliveryError(f"schema 引用不存在：{ref}")
        value = value[key]
    if not isinstance(value, Mapping):
        raise DeliveryError(f"schema 引用没有指向对象：{ref}")
    return value


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise DeliveryError(f"schema 使用了不支持的类型：{expected}")


def _validate_schema_value(
    value: Any,
    schema: Mapping[str, Any],
    *,
    root: Mapping[str, Any],
    location: str,
) -> None:
    if "$ref" in schema:
        _validate_schema_value(
            value,
            _resolve_local_ref(root, str(schema["$ref"])),
            root=root,
            location=location,
        )
        return

    if "const" in schema and value != schema["const"]:
        raise DeliveryError(f"{location} 必须等于 {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise DeliveryError(f"{location} 的值不受支持：{value!r}")

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else list(expected)
        if not any(_matches_type(value, item) for item in expected_types):
            raise DeliveryError(
                f"{location} 类型错误，应为 {' 或 '.join(expected_types)}"
            )

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if minimum is not None and len(value) < minimum:
            raise DeliveryError(f"{location} 不能为空")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(str(pattern), value) is None:
            raise DeliveryError(f"{location} 不符合格式要求")

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise DeliveryError(f"{location} 不能小于 {minimum}")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(value) < minimum:
            raise DeliveryError(f"{location} 至少需要 {minimum} 项")
        maximum = schema.get("maxItems")
        if maximum is not None and len(value) > maximum:
            raise DeliveryError(f"{location} 最多允许 {maximum} 项")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                raise DeliveryError(f"{location} 不能包含重复项")
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_value(
                    item,
                    item_schema,
                    root=root,
                    location=f"{location}[{index}]",
                )

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise DeliveryError(f"{location} 缺少字段 {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise DeliveryError(
                    f"{location} 包含未定义字段：{'、'.join(extras)}"
                )
        for key, item_schema in properties.items():
            if key in value and isinstance(item_schema, Mapping):
                _validate_schema_value(
                    value[key],
                    item_schema,
                    root=root,
                    location=f"{location}.{key}",
                )


def validate_json_schema(
    value: Mapping[str, Any],
    schema_path: Path,
    *,
    label: str,
) -> None:
    schema = _load_json(schema_path)
    _validate_schema_value(value, schema, root=schema, location=label)


def _regenerate_search_receipt(receipt: Mapping[str, Any]) -> dict[str, object]:
    request = receipt["request"]
    if not isinstance(request, Mapping):
        raise DeliveryError("检索回执 request 必须是对象")
    hits, issues = search_library(
        query=str(receipt["query"]),
        assets=list(request["assets"]),
        content_type=request["content_type"],
        limit=int(request["limit"]),
        roles=list(request["roles"]),
        benefit_recipients=list(request["benefit_recipients"]),
    )
    return build_search_receipt(
        query=str(receipt["query"]),
        assets=list(request["assets"]),
        content_type=request["content_type"],
        limit=int(request["limit"]),
        roles=list(request["roles"]),
        benefit_recipients=list(request["benefit_recipients"]),
        hits=hits,
        issues=issues,
    )


def _validate_search_receipt(
    receipt: Mapping[str, Any],
    *,
    label: str,
    expected_assets: set[str],
) -> None:
    validate_json_schema(receipt, SEARCH_SCHEMA_PATH, label=label)
    if receipt["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise DeliveryError(f"{label} schema_version 不受支持")
    request = receipt["request"]
    assets = set(request["assets"])
    if assets != expected_assets or len(request["assets"]) != len(expected_assets):
        expected = "、".join(sorted(expected_assets))
        raise DeliveryError(f"{label} 必须且只能检索 {expected}")
    if request["limit"] < 3:
        raise DeliveryError(f"{label} 必须至少请求 3 个候选")
    expected = _regenerate_search_receipt(receipt)
    if dict(receipt) != expected:
        raise DeliveryError(
            f"{label} 不是当前案例库与正式检索器生成的原始结果"
        )


def _candidate_map(receipt: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(candidate["candidate_id"]): candidate
        for candidate in receipt["candidates"]
    }


def _validate_source_location(location: str, *, label: str) -> None:
    if location == "current_material" or re.match(r"https?://", location):
        return
    if not Path(location).exists():
        raise DeliveryError(f"{label} 指向的本地来源不存在：{location}")


def _validate_decision_coverage(
    decisions: Sequence[Mapping[str, Any]],
    candidates: Mapping[str, Mapping[str, Any]],
    *,
    label: str,
) -> None:
    identifiers = [str(decision["candidate_id"]) for decision in decisions]
    if len(identifiers) != len(set(identifiers)):
        raise DeliveryError(f"{label} 不能重复判断同一候选")
    unknown = sorted(set(identifiers) - set(candidates))
    if unknown:
        raise DeliveryError(f"{label} 引用了检索结果之外的候选：{'、'.join(unknown)}")
    required_count = min(2, len(candidates))
    if len(decisions) < required_count:
        raise DeliveryError(
            f"{label} 返回了 {len(candidates)} 个候选，至少要实际比较 {required_count} 个"
        )
    if not candidates and decisions:
        raise DeliveryError(f"{label} 没有候选时不能生成采用判断")


def _validate_materials(record: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    materials = record["materials"]
    identifiers = [str(item["material_id"]) for item in materials]
    if len(identifiers) != len(set(identifiers)):
        raise DeliveryError("materials.material_id 不能重复")
    material_map = {str(item["material_id"]): item for item in materials}
    primary_id = str(record["artifact"]["primary_reader_result_id"])
    primary = material_map.get(primary_id)
    if primary is None:
        raise DeliveryError("primary_reader_result_id 没有对应的材料")
    if primary["kind"] != "reader_result" or primary["placement"] != "lead":
        raise DeliveryError("主要读者结果必须是 reader_result，并放在 lead")
    lead_materials = [item for item in materials if item["placement"] == "lead"]
    if len(lead_materials) != 1 or lead_materials[0]["material_id"] != primary_id:
        raise DeliveryError("开头只能放一项主要读者结果，证明和内部机制必须后置或省略")
    for index, item in enumerate(materials):
        _validate_source_location(
            str(item["source_location"]),
            label=f"materials[{index}].source_location",
        )
    return material_map


def _validate_opening(record: Mapping[str, Any]) -> None:
    artifact = record["artifact"]
    draft = str(artifact["draft"])
    opening = str(artifact["opening"])
    continuation = str(artifact["continuation"])
    if not draft.startswith(opening):
        raise DeliveryError("artifact.opening 必须是正文实际第一句")
    remainder = draft[len(opening) :].lstrip()
    if not remainder.startswith(continuation):
        raise DeliveryError("artifact.continuation 必须紧接正文第一句")


def _validate_facts(record: Mapping[str, Any]) -> None:
    draft = str(record["artifact"]["draft"])
    for index, fact in enumerate(record["facts"]):
        if str(fact["draft_excerpt"]) not in draft:
            raise DeliveryError(f"facts[{index}].draft_excerpt 不在正文中")
        _validate_source_location(
            str(fact["source_location"]),
            label=f"facts[{index}].source_location",
        )


def _validate_full_case_decisions(record: Mapping[str, Any]) -> None:
    draft = str(record["artifact"]["draft"])
    candidates = _candidate_map(record["full_case_search"])
    decisions = record["full_case_decisions"]
    _validate_decision_coverage(
        decisions,
        candidates,
        label="full_case_decisions",
    )
    for index, decision in enumerate(decisions):
        candidate = candidates[str(decision["candidate_id"])]
        if decision["status"] == "adopted":
            for field in ("source_excerpt", "source_mechanism", "draft_excerpt", "effect"):
                if not str(decision[field]).strip():
                    raise DeliveryError(f"full_case_decisions[{index}].{field} 不能为空")
            if str(decision["source_excerpt"]) not in str(candidate["text"]):
                raise DeliveryError(
                    f"full_case_decisions[{index}].source_excerpt 不在案例原文中"
                )
            if str(decision["draft_excerpt"]) not in draft:
                raise DeliveryError(
                    f"full_case_decisions[{index}].draft_excerpt 不在正文中"
                )
            if decision["distinct_from_template"] is not True:
                raise DeliveryError(
                    f"full_case_decisions[{index}] 没有证明影响区别于模板"
                )
        else:
            for field in ("source_excerpt", "source_mechanism", "draft_excerpt", "effect"):
                if str(decision[field]):
                    raise DeliveryError(
                        f"full_case_decisions[{index}] 未采用时不能填写 {field}"
                    )
            if decision["distinct_from_template"] is not False:
                raise DeliveryError(
                    f"full_case_decisions[{index}] 未采用时 distinct_from_template 必须为 false"
                )


def _validate_relation_mappings(
    mappings: Sequence[Mapping[str, Any]],
    *,
    allowed_relations: Sequence[str],
    required_exact: bool,
    material_ids: set[str],
    label: str,
) -> None:
    relations = [str(mapping["relation"]) for mapping in mappings]
    if len(relations) != len(set(relations)):
        raise DeliveryError(f"{label} 不能重复映射同一关系")
    if required_exact and set(relations) != set(allowed_relations):
        raise DeliveryError(f"{label} 必须逐项映射候选的全部必须关系")
    if not required_exact and not set(relations).issubset(set(allowed_relations)):
        raise DeliveryError(f"{label} 使用了候选没有声明的增强信息")
    for mapping in mappings:
        unknown = sorted(set(mapping["material_ids"]) - material_ids)
        if unknown:
            raise DeliveryError(f"{label} 引用了不存在的材料：{'、'.join(unknown)}")


def _validate_hook_decisions(
    record: Mapping[str, Any],
    material_map: Mapping[str, Mapping[str, Any]],
) -> None:
    artifact = record["artifact"]
    candidates = _candidate_map(record["hook_search"])
    decisions = record["hook_decisions"]
    _validate_decision_coverage(decisions, candidates, label="hook_decisions")
    adopted = [decision for decision in decisions if decision["status"] == "adopted"]
    if len(adopted) > 1:
        raise DeliveryError("一个成品最多采用一个外部钩子")
    material_ids = set(material_map)
    for index, decision in enumerate(decisions):
        candidate = candidates[str(decision["candidate_id"])]
        if decision["status"] == "adopted":
            for field in (
                "source_excerpt",
                "source_opening_action",
                "opening",
                "continuation",
                "effect",
            ):
                if not str(decision[field]).strip():
                    raise DeliveryError(f"hook_decisions[{index}].{field} 不能为空")
            if str(decision["source_excerpt"]) not in str(candidate["text"]):
                raise DeliveryError(
                    f"hook_decisions[{index}].source_excerpt 不在开头案例原文中"
                )
            if decision["source_opening_action"] not in candidate["hook_techniques"]:
                raise DeliveryError(
                    f"hook_decisions[{index}].source_opening_action 不是候选声明的开头动作"
                )
            if decision["opening"] != artifact["opening"]:
                raise DeliveryError(f"hook_decisions[{index}].opening 不是正文实际第一句")
            if decision["continuation"] != artifact["continuation"]:
                raise DeliveryError(f"hook_decisions[{index}].continuation 不是正文实际承接句")
            if not decision["improvement_dimensions"]:
                raise DeliveryError(
                    f"hook_decisions[{index}] 没有记录可辨认的表达改善"
                )
            _validate_relation_mappings(
                decision["required_relation_mappings"],
                allowed_relations=candidate["required_relations"],
                required_exact=True,
                material_ids=material_ids,
                label=f"hook_decisions[{index}].required_relation_mappings",
            )
            _validate_relation_mappings(
                decision["optional_amplifier_mappings"],
                allowed_relations=candidate["optional_amplifiers"],
                required_exact=False,
                material_ids=material_ids,
                label=f"hook_decisions[{index}].optional_amplifier_mappings",
            )
        else:
            for field in (
                "source_excerpt",
                "source_opening_action",
                "opening",
                "continuation",
                "effect",
            ):
                if str(decision[field]):
                    raise DeliveryError(
                        f"hook_decisions[{index}] 未采用时不能填写 {field}"
                    )
            for field in (
                "required_relation_mappings",
                "optional_amplifier_mappings",
                "improvement_dimensions",
            ):
                if decision[field]:
                    raise DeliveryError(
                        f"hook_decisions[{index}] 未采用时不能填写 {field}"
                    )


def _validate_language_and_voice(record: Mapping[str, Any]) -> None:
    draft = str(record["artifact"]["draft"])
    material_text = "\n".join(str(item["content"]) for item in record["materials"])
    for index, decision in enumerate(record["language_decisions"]):
        if str(decision["source_expression"]) not in material_text:
            raise DeliveryError(
                f"language_decisions[{index}].source_expression 不在正式材料中"
            )
        if str(decision["reader_expression"]) not in draft:
            raise DeliveryError(
                f"language_decisions[{index}].reader_expression 不在正文中"
            )
    for index, source in enumerate(record["voice_sources"]):
        _validate_source_location(
            str(source["location"]),
            label=f"voice_sources[{index}].location",
        )


def validate_record(record: Mapping[str, Any]) -> None:
    validate_json_schema(record, RECORD_SCHEMA_PATH, label="record")
    if record["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise DeliveryError("record.schema_version 不受支持")
    validate_json_schema(
        record["full_case_search"],
        SEARCH_SCHEMA_PATH,
        label="full_case_search",
    )
    full_assets = set(record["full_case_search"]["request"]["assets"])
    if len(full_assets) != 1 or not full_assets.issubset({"short", "article"}):
        raise DeliveryError("full_case_search 必须且只能选择 short 或 article 之一")
    _validate_search_receipt(
        record["full_case_search"],
        label="full_case_search",
        expected_assets=full_assets,
    )
    _validate_search_receipt(
        record["hook_search"],
        label="hook_search",
        expected_assets={"hook"},
    )
    material_map = _validate_materials(record)
    _validate_opening(record)
    _validate_facts(record)
    _validate_full_case_decisions(record)
    _validate_hook_decisions(record, material_map)
    _validate_language_and_voice(record)


def _markdown_location(location: str, label: str) -> str:
    if location == "current_material":
        return "当前材料"
    if re.match(r"https?://", location):
        return f"[{label}]({location})"
    path = Path(location)
    if path.exists():
        return f"[{label}](<{path.resolve().as_posix()}>)"
    return location


def _candidate_links(candidate: Mapping[str, Any]) -> str:
    case_file = _markdown_location(str(candidate["case_file"]), str(candidate["title"]))
    source = _markdown_location(str(candidate["source"]), "原始来源").rstrip("。")
    return f"{case_file}；{source}"


def _code_fence(text: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _render_material_choices(record: Mapping[str, Any]) -> list[str]:
    artifact = record["artifact"]
    primary_id = artifact["primary_reader_result_id"]
    primary = next(
        item for item in record["materials"] if item["material_id"] == primary_id
    )
    lines = [
        "### 写作目标与取舍",
        "",
        f"目标读者是{artifact['target_reader']}。本篇只把“{primary['content']}”作为第一屏的主要变化。{artifact['editorial_choice']}",
        "",
    ]
    other_materials = [
        item for item in record["materials"] if item["material_id"] != primary_id
    ]
    if other_materials:
        placement_labels = {
            "lead": "进入开头",
            "proof": "用于证明",
            "later": "后置解释",
            "omitted": "不进入正文",
        }
        for item in other_materials:
            lines.append(
                f"- {item['content']}：{placement_labels[item['placement']]}。{item['reason']}"
            )
        lines.append("")
    return lines


def _render_facts(record: Mapping[str, Any]) -> list[str]:
    lines = ["### 事实与来源", ""]
    for fact in record["facts"]:
        source = _markdown_location(str(fact["source_location"]), "来源")
        kind = SOURCE_KINDS[str(fact["source_kind"])]
        lines.append(
            f"- {fact['statement']}。来源：{source}（{kind}）；支撑正文“{fact['draft_excerpt']}”。{fact['effect']}"
        )
    lines.append("")
    return lines


def _render_full_cases(record: Mapping[str, Any]) -> list[str]:
    candidates = _candidate_map(record["full_case_search"])
    lines = ["### 完整内容案例", ""]
    if not record["full_case_decisions"]:
        lines.extend(["已检索，未采用：当前条件下没有合适案例。", ""])
        return lines
    for decision in record["full_case_decisions"]:
        candidate = candidates[str(decision["candidate_id"])]
        links = _candidate_links(candidate)
        if decision["status"] == "adopted":
            lines.append(
                f"- 已检索并采用：{links}。借鉴的是{decision['source_mechanism']}，具体改变正文“{decision['draft_excerpt']}”。{decision['effect']}反事实检查：{decision['counterfactual']}这项变化已确认不是专项模板或当前材料本来就会产生。"
            )
        else:
            lines.append(
                f"- 已检索，未采用：{links}。{decision['reason']}反事实检查：{decision['counterfactual']}"
            )
    lines.append("")
    return lines


def _render_hook(record: Mapping[str, Any]) -> list[str]:
    candidates = _candidate_map(record["hook_search"])
    materials = {item["material_id"]: item for item in record["materials"]}
    lines = ["### 钩子", ""]
    if not record["hook_decisions"]:
        lines.extend(["已检索，未采用：当前条件下没有合适的开头案例。", ""])
        return lines
    for decision in record["hook_decisions"]:
        candidate = candidates[str(decision["candidate_id"])]
        links = _candidate_links(candidate)
        if decision["status"] == "adopted":
            mappings = []
            for mapping in decision["required_relation_mappings"]:
                evidence = "、".join(
                    str(materials[item_id]["content"])
                    for item_id in mapping["material_ids"]
                )
                mappings.append(f"“{mapping['relation']}”由“{evidence}”承担")
            amplifiers = []
            for mapping in decision["optional_amplifier_mappings"]:
                evidence = "、".join(
                    str(materials[item_id]["content"])
                    for item_id in mapping["material_ids"]
                )
                amplifiers.append(f"“{mapping['relation']}”由“{evidence}”承担")
            dimensions = "、".join(
                IMPROVEMENT_LABELS[str(item)]
                for item in decision["improvement_dimensions"]
            )
            amplifier_text = "；".join(amplifiers) if amplifiers else "没有使用可选增强信息"
            lines.append(
                f"- 已检索并采用：{links}。必须关系对应为：{'；'.join(mappings)}。{amplifier_text}。来源采用的开头动作是{decision['source_opening_action']}；正文以“{decision['opening']}”开头，并由“{decision['continuation']}”承接。它实际改善了{dimensions}：{decision['effect']}"
            )
        else:
            lines.append(f"- 已检索，未采用：{links}。{decision['reason']}")
    lines.append("")
    return lines


def _render_language(record: Mapping[str, Any]) -> list[str]:
    lines = ["### 语言与删减", ""]
    if record["language_decisions"]:
        for decision in record["language_decisions"]:
            lines.append(
                f"- 把“{decision['source_expression']}”处理为“{decision['reader_expression']}”。{decision['effect']}"
            )
    if record["omissions"]:
        for omission in record["omissions"]:
            lines.append(f"- 没有写入“{omission['content']}”。{omission['reason']}")
    if not record["language_decisions"] and not record["omissions"]:
        lines.append("本稿没有额外术语转换或材料删减。")
    lines.append("")
    return lines


def _render_voice_format(record: Mapping[str, Any]) -> list[str]:
    if (
        not record["voice_sources"]
        and not record["format_requirements"]
        and not record["promotion_contract"]
    ):
        return []
    lines = ["### 作者声音、格式与宣发合同", ""]
    for source in record["voice_sources"]:
        location = _markdown_location(str(source["location"]), "声音证据")
        lines.append(
            f"- 作者声音：{location}。采用了{source['features']}；{source['effect']}"
        )
    if record["format_requirements"]:
        lines.append("- 明确格式：" + "；".join(record["format_requirements"]))
    if record["promotion_contract"]:
        lines.append("- 宣发合同：" + str(record["promotion_contract"]))
    lines.append("")
    return lines


def render_delivery(
    record: Mapping[str, Any],
    *,
    include_explanation: bool = True,
) -> str:
    validate_record(record)
    draft = str(record["artifact"]["draft"])
    fence = _code_fence(draft)
    lines = ["## 写作成品", "", fence, draft, fence]
    if not include_explanation:
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(["", "## 写作说明", ""])
    lines.extend(_render_material_choices(record))
    lines.extend(_render_facts(record))
    lines.extend(_render_full_cases(record))
    lines.extend(_render_hook(record))
    lines.extend(_render_language(record))
    lines.extend(_render_voice_format(record))
    return "\n".join(lines).rstrip() + "\n"


def _read_record(location: str) -> dict[str, Any]:
    if location == "-":
        raw = sys.stdin.read()
        source = "标准输入"
    else:
        path = Path(location)
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise DeliveryError(f"无法读取写作执行记录：{path}: {exc}") from exc
        source = str(path)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeliveryError(f"写作执行记录不是有效 JSON（{source}）：{exc}") from exc
    if not isinstance(value, dict):
        raise DeliveryError("写作执行记录根节点必须是对象")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="校验写作执行记录并生成可追溯交付")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument(
        "--record",
        required=True,
        help="写作执行记录 JSON 路径；使用 - 从标准输入读取",
    )
    render = commands.add_parser("render")
    render.add_argument(
        "--record",
        required=True,
        help="写作执行记录 JSON 路径；使用 - 从标准输入读取",
    )
    render.add_argument(
        "--copy-only",
        action="store_true",
        help="用户明确只要可复制正文时省略写作说明",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        record = _read_record(args.record)
        if args.command == "validate":
            validate_record(record)
            print(
                "写作执行记录有效："
                f"完整案例判断 {len(record['full_case_decisions'])} 项，"
                f"钩子判断 {len(record['hook_decisions'])} 项。"
            )
        else:
            print(
                render_delivery(
                    record,
                    include_explanation=not args.copy_only,
                ),
                end="",
            )
    except DeliveryError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
