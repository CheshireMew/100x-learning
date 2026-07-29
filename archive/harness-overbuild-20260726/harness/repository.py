from __future__ import annotations

import re
from pathlib import Path

from .result import ValidationReport


LOCAL_RESOURCE_RE = re.compile(
    r"`((?:references|scripts|harness)/[^`]+|harness|System Knowledge/[^`]+)`"
)
REQUIRED_AUDIENCE_LANGUAGE_GUIDANCE = {
    "SKILL.md": (
        "工作包与成品使用不同语言",
        "这些英文键名和过程标签只服务内部协作",
    ),
    "references/content-writing.md": (
        "内容真源 + 当前作者声音 + 对应写作模板 + 同类型完整案例",
        "重要句子至少完成一种实际作用",
        "Harness 只核对资源、来源、授权和结构是否进入同一个生产输入",
    ),
    "references/github-project-short-content.md": (
        "本文件是专项模板",
        "模板和完整案例同时进入同一个写作输入",
    ),
    "references/content-case-retrieval.md": (
        "完整案例是写作生产者的正式输入",
        "生产者直接使用完整案例",
    ),
    "references/social-content-distribution.md": (
        "这份计划只服务内部选择和校验",
    ),
}


def validate_repository(root: Path) -> ValidationReport:
    report = ValidationReport()
    root = root.resolve()
    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        report.error("repository.missing_skill", "缺少 SKILL.md", "SKILL.md")
        return report

    skill_text = skill_path.read_text(encoding="utf-8-sig")
    if not skill_text.startswith("---\n") and not skill_text.startswith("---\r\n"):
        report.error("repository.missing_frontmatter", "SKILL.md 缺少 frontmatter", "SKILL.md")

    resources = sorted(set(LOCAL_RESOURCE_RE.findall(skill_text)))
    for resource in resources:
        if not (root / Path(resource)).exists():
            report.error(
                "repository.missing_resource",
                f"SKILL.md 引用的资源不存在：{resource}",
                resource,
            )

    for relative, markers in REQUIRED_AUDIENCE_LANGUAGE_GUIDANCE.items():
        path = root / relative
        if not path.is_file():
            report.error(
                "repository.missing_audience_language_guidance",
                f"缺少面向读者的语言转换规则：{relative}",
                relative,
            )
            continue
        text = path.read_text(encoding="utf-8-sig")
        for marker in markers:
            if marker not in text:
                report.error(
                    "repository.incomplete_audience_language_guidance",
                    f"面向读者的语言转换规则不完整：{marker}",
                    relative,
                )

    home_path = root / "System Knowledge" / "Home.md"
    if not home_path.exists():
        report.warning(
            "repository.kb_unavailable",
            "System Knowledge/Home.md 不存在；运行时应跳过本地检索并禁止猜测路径",
            "System Knowledge/Home.md",
        )

    report.details["root"] = str(root)
    report.details["resource_count"] = len(resources)
    return report
