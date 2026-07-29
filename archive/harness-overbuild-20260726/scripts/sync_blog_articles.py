from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTICLE_ROOT = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Articles"
    / "Cheshire"
    / "Blog"
)
DECISIONS_PATH = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Articles"
    / "Cheshire"
    / "blog-article-decisions.json"
)
AUDIT_PATH = (
    PROJECT_ROOT
    / "System Knowledge"
    / "20-Sources"
    / "Articles"
    / "Cheshire"
    / "博客文章审计.md"
)
API_ROOT = "https://blog.blacknico.com/wp-json/wp/v2"
USER_AGENT = "100x-learning local article archive"

AUTHORSHIP_VALUES = {
    "本人主导",
    "人机共写",
    "AI 主笔",
    "翻译",
    "资料整理",
    "待确认",
}
REFERENCE_VALUES = {"case", "archive"}
CONTENT_TYPES = {
    "项目与产品介绍",
    "概念与机制解释",
    "教程与操作指南",
    "清单与资源推荐",
    "事件与商业故事",
    "观点与趋势判断",
    "行业与投资分析",
    "个人观察与实测",
}
CONTENT_TYPE_DEFAULTS = {
    "项目与产品介绍": (
        "介绍项目或产品",
        ("用户问题", "产品角色", "主要能力", "可见结果"),
    ),
    "概念与机制解释": (
        "解释概念或机制",
        ("现实问题", "关键条件", "作用机制", "实际影响"),
    ),
    "教程与操作指南": (
        "编写教程或操作指南",
        ("目标任务", "操作顺序", "关键参数", "完成结果"),
    ),
    "清单与资源推荐": (
        "整理清单或资源推荐",
        ("选择标准", "分类条目", "各自用途", "使用入口"),
    ),
    "事件与商业故事": (
        "讲述事件或商业故事",
        ("触发事件", "行动与阻碍", "关键选择", "结果与影响"),
    ),
    "观点与趋势判断": (
        "表达观点或趋势判断",
        ("可观察变化", "作者判断", "支撑理由", "适用边界"),
    ),
    "行业与投资分析": (
        "分析行业或投资问题",
        ("现实问题", "数量或机制", "方案比较", "判断与条件"),
    ),
    "个人观察与实测": (
        "讲述个人经历或实测",
        ("真实触发", "实际操作", "阻力与调整", "结果与判断"),
    ),
}

class BlogArchiveError(ValueError):
    pass


def _request_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    return response.json(), response.headers


def fetch_categories() -> dict[int, str]:
    payload, _ = _request_json(
        f"{API_ROOT}/categories",
        {"per_page": 100, "_fields": "id,name"},
    )
    return {int(item["id"]): html.unescape(item["name"]) for item in payload}


def fetch_posts() -> list[dict[str, Any]]:
    categories = fetch_categories()
    posts: list[dict[str, Any]] = []
    page = 1
    while True:
        payload, headers = _request_json(
            f"{API_ROOT}/posts",
            {
                "per_page": 100,
                "page": page,
                "_fields": "id,slug,link,title,content,categories",
            },
        )
        for post in payload:
            post["title_text"] = html.unescape(post["title"]["rendered"]).strip()
            post["category_names"] = [
                categories[int(category_id)]
                for category_id in post.get("categories", [])
                if int(category_id) in categories
            ]
            posts.append(post)
        total_pages = int(headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break
        page += 1
    posts.sort(key=lambda item: int(item["id"]))
    return posts


def _normalize_image_sources(soup: BeautifulSoup) -> None:
    for image in soup.find_all("img"):
        for attribute in ("data-src", "data-original", "data-lazy-src"):
            candidate = image.get(attribute)
            if candidate:
                image["src"] = candidate
                break
        image.attrs = {
            key: value
            for key, value in image.attrs.items()
            if key in {"src", "alt", "title"}
        }


def html_to_markdown(rendered: str) -> str:
    soup = BeautifulSoup(html.unescape(rendered), "html.parser")
    for unwanted in soup.find_all(["script", "style", "noscript"]):
        unwanted.decompose()
    _normalize_image_sources(soup)
    text = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=["figure"],
    )
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    footer_patterns = (
        r"\n#{1,6}\s*🤝\s*创作不易.*$",
        r"\n#{1,6}\s*联系方式\s*$.*",
        r"\n正文完\s*$.*",
    )
    for pattern in footer_patterns:
        match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
        if match:
            text = text[: match.start()].rstrip()
    return text + "\n"


def load_decisions(path: Path = DECISIONS_PATH) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise BlogArchiveError(f"判定文件不存在：{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    posts = payload.get("posts")
    if not isinstance(posts, dict):
        raise BlogArchiveError("判定文件缺少 posts 对象")
    return posts


def validate_decisions(
    posts: list[dict[str, Any]],
    decisions: dict[str, dict[str, str]],
) -> list[str]:
    issues: list[str] = []
    remote_slugs = {post["slug"] for post in posts}
    decision_slugs = set(decisions)
    for slug in sorted(remote_slugs - decision_slugs):
        issues.append(f"缺少文章判定：{slug}")
    for slug in sorted(decision_slugs - remote_slugs):
        issues.append(f"判定文件存在网站中没有的文章：{slug}")
    for slug in sorted(remote_slugs & decision_slugs):
        decision = decisions[slug]
        authorship = decision.get("authorship")
        reference = decision.get("reference_value")
        content_type = decision.get("content_type")
        reason = decision.get("reason")
        if authorship not in AUTHORSHIP_VALUES:
            issues.append(f"{slug}: authorship 无效：{authorship}")
        if reference not in REFERENCE_VALUES:
            issues.append(f"{slug}: reference_value 无效：{reference}")
        if content_type not in CONTENT_TYPES:
            issues.append(f"{slug}: content_type 无效：{content_type}")
        if not isinstance(reason, str) or not reason.strip():
            issues.append(f"{slug}: reason 不能为空")
    return issues


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _yaml_list(values: list[str] | tuple[str, ...]) -> str:
    return "[" + ", ".join(_yaml_scalar(value) for value in values) + "]"


def _topics(post: dict[str, Any]) -> list[str]:
    values = [*post["category_names"], post["title_text"]]
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def render_article(
    post: dict[str, Any],
    decision: dict[str, str],
) -> str:
    content_type = decision["content_type"]
    writing_task, structure = CONTENT_TYPE_DEFAULTS[content_type]
    lines = [
        "---",
        f"authorship: {_yaml_scalar(decision['authorship'])}",
        f"reference_value: {_yaml_scalar(decision['reference_value'])}",
        f"content_type: {_yaml_scalar(content_type)}",
        f"source_url: {_yaml_scalar(post['link'])}",
    ]
    if decision["reference_value"] == "case":
        lines.extend(
            [
                f"writing_task: {_yaml_scalar(writing_task)}",
                f"topics: {_yaml_list(_topics(post))}",
                f"structure: {_yaml_list(list(structure))}",
            ]
        )
    lines.extend(["---", "", f"# {post['title_text']}", ""])
    lines.append(html_to_markdown(post["content"]["rendered"]).rstrip())
    if decision["reference_value"] == "case":
        lines.extend(
            [
                "",
                "<!-- content-case-notes -->",
                "",
                "## 可以参考什么",
                "",
                "参考正文怎样完成“"
                + " → ".join(structure)
                + "”的推进。案例只提供组织与表达，当前写作仍以当前内容真源为准。",
                "",
                "## 适用场景",
                "",
                writing_task + "，且需要完整文章作为正文结构参考时。",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _escape_table(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ")


def render_audit(
    posts: list[dict[str, Any]],
    decisions: dict[str, dict[str, str]],
) -> str:
    authorship_counts = Counter(
        decisions[post["slug"]]["authorship"] for post in posts
    )
    reference_counts = Counter(
        decisions[post["slug"]]["reference_value"] for post in posts
    )
    lines = [
        "# 博客文章审计",
        "",
        "这里核对个人博客的全部文章正文、来源性质和案例去向。日期和站内作者名不参与筛选；写作检索使用内容类型、写作任务、主题和结构。",
        "",
        f"网站文章：{len(posts)} 篇；进入参考案例库：{reference_counts['case']} 篇；仅保存正文：{reference_counts['archive']} 篇。",
        "",
        "来源性质：" + "；".join(
            f"{key} {authorship_counts[key]} 篇"
            for key in sorted(authorship_counts)
        )
        + "。",
        "",
        "完整正文补全记录单独保存在 [博客正文补全清单](<博客正文补全清单.md>)。",
        "",
        "## 全部文章的来源性质与去向",
        "",
        "| 正文 | 内容类型 | 来源性质 | 去向 | 判断依据 | 原文 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for post in sorted(posts, key=lambda item: item["title_text"]):
        decision = decisions[post["slug"]]
        local = f"Blog/{post['slug']}.md"
        destination = (
            "参考案例库"
            if decision["reference_value"] == "case"
            else "仅保存正文"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"[{_escape_table(post['title_text'])}](<{local}>)",
                    decision["content_type"],
                    decision["authorship"],
                    destination,
                    _escape_table(decision["reason"]),
                    f"[网站]({post['link']})",
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def sync(posts: list[dict[str, Any]], decisions: dict[str, dict[str, str]]) -> None:
    issues = validate_decisions(posts, decisions)
    if issues:
        raise BlogArchiveError("\n".join(issues))
    ARTICLE_ROOT.mkdir(parents=True, exist_ok=True)
    for post in posts:
        target = ARTICLE_ROOT / f"{post['slug']}.md"
        target.write_text(
            render_article(post, decisions[post["slug"]]),
            encoding="utf-8",
        )
    AUDIT_PATH.write_text(
        render_audit(posts, decisions),
        encoding="utf-8",
    )
    print(f"正文已同步：{len(posts)} 篇 -> {ARTICLE_ROOT}")
    print(f"审计已更新：{AUDIT_PATH}")


def validate_local(
    posts: list[dict[str, Any]],
    decisions: dict[str, dict[str, str]],
) -> list[str]:
    issues = validate_decisions(posts, decisions)
    expected = {f"{post['slug']}.md" for post in posts}
    actual = (
        {path.name for path in ARTICLE_ROOT.glob("*.md")}
        if ARTICLE_ROOT.exists()
        else set()
    )
    for name in sorted(expected - actual):
        issues.append(f"缺少本地正文：{name}")
    for name in sorted(actual - expected):
        issues.append(f"本地存在网站中没有的正文，需要人工归档：{name}")
    post_by_slug = {post["slug"]: post for post in posts}
    for name in sorted(expected & actual):
        slug = name[:-3]
        expected_text = render_article(post_by_slug[slug], decisions[slug])
        actual_text = (ARTICLE_ROOT / name).read_text(encoding="utf-8")
        if actual_text != expected_text:
            issues.append(f"本地正文不是网站当前版本：{name}")
    expected_audit = render_audit(posts, decisions)
    if not AUDIT_PATH.exists():
        issues.append(f"缺少博客文章审计：{AUDIT_PATH}")
    elif AUDIT_PATH.read_text(encoding="utf-8") != expected_audit:
        issues.append(f"博客文章审计需要更新：{AUDIT_PATH}")
    return issues


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从个人博客同步完整正文，并核对来源性质和案例去向。"
    )
    parser.add_argument(
        "command",
        choices=("sync", "validate"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        posts = fetch_posts()
        decisions = load_decisions()
        if args.command == "sync":
            sync(posts, decisions)
            return 0
        issues = validate_local(posts, decisions)
        if issues:
            print("\n".join(issues), file=sys.stderr)
            return 1
        print(f"博客正文有效：{len(posts)} 篇，清单、正文与网站当前版本一致。")
        return 0
    except (BlogArchiveError, OSError, requests.RequestException, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
