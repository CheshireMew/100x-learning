from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

try:
    from scripts.marktree_integration import managed_write_text
    from scripts.private_library import (
        LibraryError,
        LibraryLayout,
        resolve_library_root,
        validate_library,
    )
except ModuleNotFoundError:
    from marktree_integration import managed_write_text
    from private_library import (
        LibraryError,
        LibraryLayout,
        resolve_library_root,
        validate_library,
    )


OUTPUT_RELATIVE = Path("40-Outputs/Writing")
SOCIAL_CASE_RELATIVE = Path(
    "20-Sources/Social Posts/Content Cases/完整短内容"
)
CONFIG_RELATIVE = Path("60-Systems/Writing/writing-memory.json")
INDEX_RELATIVE = Path("60-Systems/Writing/published-content-index.jsonl")
X_SNOWFLAKE_EPOCH_MS = 1_288_834_974_657

FINAL_OUTPUT_STATUS = {"final", "published"}
FIRST_PARTY_OUTPUT_SOURCE = {
    "user-confirmed",
    "published-article",
    "published-post",
    "published-thread",
}
SUPPORTED_FORMATS = {
    "article",
    "original",
    "quote",
    "resource",
    "thread",
    "product",
    "short-post",
}
FORMAT_ALIASES = {
    "post": "original",
    "original-post": "original",
    "quote-post": "quote",
    "resource-share": "resource",
    "product-post": "product",
    "short": "short-post",
}
SUPPORTED_SEARCH_PURPOSES = {"voice", "novelty"}
SUPPORTED_WRITING_ORIGINS = {
    "human",
    "human-edited",
    "ai-generated",
    "curated",
    "translated",
    "unknown",
}
VOICE_ELIGIBLE_ORIGINS = {"human", "human-edited"}
BLOG_ORIGIN_MAP = {
    "本人主导": "human",
    "AI 主笔": "ai-generated",
    "资料整理": "curated",
    "翻译": "translated",
    "待确认": "unknown",
}


class MemoryError(ValueError):
    pass


@dataclass(frozen=True)
class WritingRecord:
    id: str
    path: str
    title: str
    format: str
    content_type: str
    publisher: str
    writing_origin: str
    voice_eligible: bool
    status: str
    updated: str
    source_url: str
    source_kind: str
    text_hash: str


@dataclass(frozen=True)
class DiscoveryReceipt:
    scanned_blog: int
    scanned_outputs: int
    scanned_social: int
    accepted_blog: int
    accepted_outputs: int
    accepted_social: int
    merged_by_url: int
    merged_by_text: int


@dataclass(frozen=True)
class SearchHit:
    record: WritingRecord
    score: float
    exact_text: bool
    opening: str
    ending: str


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.lstrip("\ufeff")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise MemoryError("frontmatter 缺少结束标记") from exc

    metadata: dict[str, str] = {}
    for raw_line in lines[1:end]:
        if not raw_line.strip() or raw_line[:1].isspace():
            continue
        if ":" not in raw_line:
            raise MemoryError(f"无法解析 frontmatter：{raw_line}")
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = _strip_quotes(value)
    return metadata, "\n".join(lines[end + 1 :]).lstrip()


def _parse_case_index_metadata(text: str, path: Path) -> dict[str, str]:
    match = re.search(
        r"\n?<!-- content-case-index\s*\n(?P<metadata>.*?)\n-->\s*$",
        text,
        re.DOTALL,
    )
    if not match:
        raise MemoryError(f"{path}: 缺少 content-case-index")

    metadata: dict[str, str] = {}
    for raw_line in match.group("metadata").splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            raise MemoryError(f"{path}: 无法解析 content-case-index：{raw_line}")
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = _strip_quotes(value)
    return metadata


def _normalize_text(value: str) -> str:
    return (
        value.replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def _section(value: str, heading: str, next_heading: str | None = None) -> str:
    start = re.search(rf"^## {re.escape(heading)}\s*$", value, re.MULTILINE)
    if not start:
        raise MemoryError(f"缺少“{heading}”")
    if next_heading:
        end = re.search(
            rf"^## {re.escape(next_heading)}\s*$",
            value[start.end() :],
            re.MULTILINE,
        )
        stop = start.end() + end.start() if end else len(value)
    else:
        stop = len(value)
    return value[start.end() : stop].strip()


def _authored_body(value: str, source_kind: str) -> str:
    if source_kind == "published-source":
        value = value.split("<!-- content-case-index", 1)[0]
    elif source_kind == "published-social":
        value = _section(value, "原帖全文")
        value = value.split("<!-- content-case-index", 1)[0]
        value = re.sub(
            r"^(?:原帖链接|来源)：\s*.+?\s*$",
            "",
            value,
            flags=re.MULTILINE,
        )
    return _normalize_text(value)


def _text_hash(value: str) -> str:
    comparable = re.sub(r"\s+", " ", _normalize_text(value)).lower()
    return hashlib.sha256(comparable.encode("utf-8")).hexdigest()


def _title(body: str, path: Path) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else path.stem


def _normalize_format(value: str, path: Path) -> str:
    normalized = FORMAT_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized:
        if normalized not in SUPPORTED_FORMATS:
            raise MemoryError(f"不支持的 format：{value}")
        return normalized

    lowered_parts = {part.lower() for part in path.parts}
    if "social" in lowered_parts:
        return "short-post"
    return "article"


def _updated(metadata: dict[str, str]) -> str:
    for key in ("published_at", "published", "updated", "date", "created"):
        value = metadata.get(key, "").strip()
        if value:
            return value
    return ""


def _writing_origin(value: str, path: Path) -> str:
    origin = value.strip().lower() or "unknown"
    if origin not in SUPPORTED_WRITING_ORIGINS:
        raise MemoryError(f"{path}: 不支持的 writing_origin：{value}")
    return origin


def _voice_eligible(
    value: str | None,
    *,
    writing_origin: str,
    path: Path,
    default: bool = False,
) -> bool:
    if value is None or not value.strip():
        eligible = default
    else:
        normalized = value.strip().lower()
        if normalized not in {"true", "false"}:
            raise MemoryError(f"{path}: voice_eligible 必须是 true 或 false")
        eligible = normalized == "true"
    if eligible and writing_origin not in VOICE_ELIGIBLE_ORIGINS:
        raise MemoryError(
            f"{path}: writing_origin={writing_origin} 不能作为长期声音证据"
        )
    return eligible


def _x_status_date(source_url: str) -> str:
    match = re.fullmatch(
        r"https://x\.com/[^/]+/status/(\d+)",
        source_url,
        re.IGNORECASE,
    )
    if not match:
        return ""
    milliseconds = (int(match.group(1)) >> 22) + X_SNOWFLAKE_EPOCH_MS
    return datetime.fromtimestamp(
        milliseconds / 1000,
        tz=timezone.utc,
    ).date().isoformat()


def _load_config(library_root: Path) -> tuple[tuple[str, ...], tuple[Path, ...]]:
    config_path = library_root.resolve() / CONFIG_RELATIVE
    if not config_path.exists():
        raise MemoryError(f"写作记忆配置不存在：{config_path}")
    try:
        values = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MemoryError(f"{config_path} 不是有效 JSON：{exc}") from exc
    prefixes = values.get("verified_first_party_url_prefixes")
    if not isinstance(prefixes, list) or not all(
        isinstance(prefix, str) and prefix.strip() for prefix in prefixes
    ):
        raise MemoryError(
            f"{config_path}: verified_first_party_url_prefixes 必须是字符串数组"
        )
    normalized_prefixes = tuple(prefix.strip().lower() for prefix in prefixes)
    if not all(
        re.fullmatch(r"https://x\.com/[a-z0-9_]+/status/", prefix)
        for prefix in normalized_prefixes
    ):
        raise MemoryError(
            f"{config_path}: 每个本人入口必须是 https://x.com/<账号>/status/"
        )
    article_roots = values.get("published_article_roots")
    if not isinstance(article_roots, list) or not all(
        isinstance(root, str) and root.strip() for root in article_roots
    ):
        raise MemoryError(
            f"{config_path}: published_article_roots 必须是字符串数组"
        )
    normalized_roots: list[Path] = []
    for raw_root in article_roots:
        relative = Path(raw_root.strip())
        if relative.is_absolute() or ".." in relative.parts:
            raise MemoryError(
                f"{config_path}: published_article_roots 必须使用私人库相对路径"
            )
        resolved = (library_root.resolve() / relative).resolve()
        try:
            resolved.relative_to(library_root.resolve())
        except ValueError as exc:
            raise MemoryError(
                f"{config_path}: 文章根目录越出私人知识库：{raw_root}"
            ) from exc
        if not resolved.is_dir():
            raise MemoryError(f"已配置的文章根目录不存在：{resolved}")
        normalized_roots.append(relative)
    return normalized_prefixes, tuple(normalized_roots)


def _relative(path: Path, library_root: Path) -> str:
    return path.resolve().relative_to(library_root.resolve()).as_posix()


def _record_from_blog(path: Path, library_root: Path) -> WritingRecord | None:
    metadata, body = _parse_frontmatter(path.read_text(encoding="utf-8-sig"))
    source_url = metadata.get("source_url", "").strip()
    if not source_url:
        return None
    source_label = metadata.get("authorship", "").strip()
    writing_origin = _writing_origin(
        BLOG_ORIGIN_MAP.get(source_label, "unknown"),
        path,
    )
    voice_eligible = _voice_eligible(
        metadata.get("voice_eligible"),
        writing_origin=writing_origin,
        path=path,
        default=writing_origin in VOICE_ELIGIBLE_ORIGINS,
    )
    normalized_body = _authored_body(body, "published-source")
    if not normalized_body:
        raise MemoryError(f"{path}: 正文为空")
    relative = _relative(path, library_root)
    return WritingRecord(
        id=source_url or f"path:{relative}",
        path=relative,
        title=_title(normalized_body, path),
        format=_normalize_format(metadata.get("format", ""), path),
        content_type=metadata.get("content_type", "").strip(),
        publisher="Cheshire Blog",
        writing_origin=writing_origin,
        voice_eligible=voice_eligible,
        status="published",
        updated=_updated(metadata),
        source_url=source_url,
        source_kind="published-source",
        text_hash=_text_hash(normalized_body),
    )


def _record_from_output(path: Path, library_root: Path) -> WritingRecord | None:
    metadata, body = _parse_frontmatter(path.read_text(encoding="utf-8-sig"))
    if metadata.get("type", "") != "writing-output":
        return None
    status = metadata.get("status", "").lower()
    source = metadata.get("source", "").lower()
    if status not in FINAL_OUTPUT_STATUS or source not in FIRST_PARTY_OUTPUT_SOURCE:
        return None
    normalized_body = _authored_body(body, "writing-output")
    if not normalized_body:
        raise MemoryError(f"{path}: 正文为空")
    source_url = (
        metadata.get("published_url", "").strip()
        or metadata.get("source_url", "").strip()
    )
    writing_origin = _writing_origin(
        metadata.get("writing_origin", "unknown"),
        path,
    )
    voice_eligible = _voice_eligible(
        metadata.get("voice_eligible"),
        writing_origin=writing_origin,
        path=path,
    )
    relative = _relative(path, library_root)
    return WritingRecord(
        id=source_url or f"path:{relative}",
        path=relative,
        title=_title(normalized_body, path),
        format=_normalize_format(metadata.get("format", ""), path),
        content_type=metadata.get("content_type", "").strip(),
        publisher=metadata.get("published_by", "").strip()
        or metadata.get("author", "").strip()
        or source,
        writing_origin=writing_origin,
        voice_eligible=voice_eligible,
        status=status,
        updated=_updated(metadata),
        source_url=source_url,
        source_kind="writing-output",
        text_hash=_text_hash(normalized_body),
    )


def _record_from_social_case(
    path: Path,
    library_root: Path,
    verified_prefixes: Sequence[str],
) -> WritingRecord | None:
    if not verified_prefixes:
        return None
    body = path.read_text(encoding="utf-8-sig")
    source_match = re.search(
        r"^(?:原帖链接|来源)：\s*(https?://\S+)\s*$",
        body,
        re.MULTILINE,
    )
    if not source_match:
        return None
    source_url = source_match.group(1).strip()
    if not any(
        source_url.lower().startswith(prefix)
        for prefix in verified_prefixes
    ):
        return None

    case_metadata = _parse_case_index_metadata(body, path)
    writing_format = case_metadata.get("writing_format", "").strip()
    if not writing_format:
        raise MemoryError(f"{path}: 本人发布案例缺少 writing_format")
    writing_origin = _writing_origin(
        case_metadata.get("writing_origin", "unknown"),
        path,
    )
    voice_eligible = _voice_eligible(
        case_metadata.get("voice_eligible"),
        writing_origin=writing_origin,
        path=path,
    )

    normalized_body = _authored_body(body, "published-social")
    if not normalized_body:
        raise MemoryError(f"{path}: 原帖全文为空")
    relative = _relative(path, library_root)
    handle_match = re.match(
        r"https://x\.com/([^/]+)/status/",
        source_url,
        re.IGNORECASE,
    )
    return WritingRecord(
        id=source_url,
        path=relative,
        title=_title(body, path),
        format=_normalize_format(writing_format, path),
        content_type=path.parent.name,
        publisher=handle_match.group(1) if handle_match else "本人发布",
        writing_origin=writing_origin,
        voice_eligible=voice_eligible,
        status="published",
        updated=_x_status_date(source_url),
        source_url=source_url,
        source_kind="published-social",
        text_hash=_text_hash(normalized_body),
    )


def _merge_record(preferred: WritingRecord, fallback: WritingRecord) -> WritingRecord:
    return replace(
        preferred,
        content_type=preferred.content_type or fallback.content_type,
        publisher=preferred.publisher or fallback.publisher,
        updated=preferred.updated or fallback.updated,
        source_url=preferred.source_url or fallback.source_url,
    )


def discover_records(
    library_root: Path,
) -> tuple[list[WritingRecord], DiscoveryReceipt]:
    library_root = library_root.resolve()
    output_root = library_root / OUTPUT_RELATIVE
    social_root = library_root / SOCIAL_CASE_RELATIVE
    verified_prefixes, published_article_roots = _load_config(library_root)
    blog_paths = sorted(
        {
            path
            for relative in published_article_roots
            for path in (library_root / relative).rglob("*.md")
        }
    )
    output_paths = (
        sorted(output_root.rglob("*.md")) if output_root.exists() else []
    )
    social_paths = (
        sorted(social_root.rglob("*.md")) if social_root.exists() else []
    )

    blog_records = [
        record
        for path in blog_paths
        if (record := _record_from_blog(path, library_root)) is not None
    ]
    output_records = [
        record
        for path in output_paths
        if (record := _record_from_output(path, library_root)) is not None
    ]
    social_records = [
        record
        for path in social_paths
        if (
            record := _record_from_social_case(
                path,
                library_root,
                verified_prefixes,
            )
        )
        is not None
    ]

    selected: list[WritingRecord] = []
    by_url: dict[str, int] = {}
    by_hash: dict[str, int] = {}
    merged_by_url = 0
    merged_by_text = 0

    # Outputs are the final user-facing truth when the same published URL also
    # exists in the source archive.
    candidates = [*output_records, *social_records, *blog_records]
    for candidate in candidates:
        existing_index = (
            by_url.get(candidate.source_url) if candidate.source_url else None
        )
        if existing_index is not None:
            current = selected[existing_index]
            selected[existing_index] = _merge_record(current, candidate)
            merged_by_url += 1
            continue

        existing_index = by_hash.get(candidate.text_hash)
        if existing_index is not None:
            current = selected[existing_index]
            selected[existing_index] = _merge_record(current, candidate)
            merged_by_text += 1
            continue

        selected.append(candidate)
        index = len(selected) - 1
        if candidate.source_url:
            by_url[candidate.source_url] = index
        by_hash[candidate.text_hash] = index

    selected.sort(
        key=lambda item: (
            item.updated != "",
            item.updated,
            item.title,
        ),
        reverse=True,
    )
    receipt = DiscoveryReceipt(
        scanned_blog=len(blog_paths),
        scanned_outputs=len(output_paths),
        scanned_social=len(social_paths),
        accepted_blog=len(blog_records),
        accepted_outputs=len(output_records),
        accepted_social=len(social_records),
        merged_by_url=merged_by_url,
        merged_by_text=merged_by_text,
    )
    return selected, receipt


def _record_json(record: WritingRecord) -> str:
    return json.dumps(asdict(record), ensure_ascii=False, sort_keys=True)


def render_index(records: Sequence[WritingRecord]) -> str:
    return "".join(f"{_record_json(record)}\n" for record in records)


def write_index(
    library_root: Path,
    records: Sequence[WritingRecord],
    config_path: Path | None = None,
) -> Path:
    index_path = library_root.resolve() / INDEX_RELATIVE
    index_path.parent.mkdir(parents=True, exist_ok=True)
    managed_write_text(
        library_root,
        index_path,
        render_index(records),
        config_path=config_path,
    )
    return index_path


def load_index(library_root: Path) -> list[WritingRecord]:
    index_path = library_root.resolve() / INDEX_RELATIVE
    if not index_path.exists():
        raise MemoryError(f"发布记录索引不存在：{index_path}")
    records: list[WritingRecord] = []
    for line_number, line in enumerate(
        index_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            values = json.loads(line)
            record = WritingRecord(**values)
        except (json.JSONDecodeError, TypeError) as exc:
            raise MemoryError(
                f"{index_path}:{line_number} 不是有效记录：{exc}"
            ) from exc
        records.append(record)
    return records


def index_is_current(library_root: Path, records: Sequence[WritingRecord]) -> bool:
    index_path = library_root.resolve() / INDEX_RELATIVE
    return (
        index_path.exists()
        and index_path.read_text(encoding="utf-8") == render_index(records)
    )


def _terms(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", value).lower()
    terms = set(re.findall(r"[a-z0-9][a-z0-9._+-]*", normalized))
    for sequence in re.findall(r"[\u3400-\u9fff]+", normalized):
        terms.add(sequence)
        if len(sequence) == 1:
            terms.add(sequence)
        else:
            terms.update(
                sequence[index : index + 2]
                for index in range(len(sequence) - 1)
            )
    return terms


def _coverage(query: str, candidates: Iterable[str]) -> float:
    query_terms = _terms(query)
    if not query_terms:
        return 0.0
    candidate_text = " ".join(candidates)
    candidate_terms = _terms(candidate_text)
    score = len(query_terms & candidate_terms) / len(query_terms)
    normalized_query = unicodedata.normalize("NFKC", query).lower().strip()
    if normalized_query and normalized_query in candidate_text.lower():
        score += 0.5
    return score


def _body(library_root: Path, record: WritingRecord) -> str:
    path = library_root.resolve() / Path(record.path)
    if not path.exists():
        raise MemoryError(f"发布记录指向的正文不存在：{path}")
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8-sig"))
    normalized = _authored_body(body, record.source_kind)
    if _text_hash(normalized) != record.text_hash:
        raise MemoryError(f"发布记录已经过期，请重建索引：{path}")
    return normalized


def _excerpt(value: str, *, from_end: bool = False, limit: int = 360) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", value).strip()
    if len(compact) <= limit:
        return compact
    if from_end:
        return "…" + compact[-limit:].lstrip()
    return compact[:limit].rstrip() + "…"


def search_memory(
    library_root: Path,
    records: Sequence[WritingRecord],
    purpose: str,
    query: str,
    format_name: str | None,
    content_type: str | None,
    limit: int,
) -> list[SearchHit]:
    if limit < 1:
        raise MemoryError("limit 必须大于 0")
    if purpose not in SUPPORTED_SEARCH_PURPOSES:
        raise MemoryError("purpose 必须是 voice 或 novelty")
    if format_name:
        format_name = _normalize_format(format_name, Path("memory.md"))
    if purpose == "voice" and not format_name:
        raise MemoryError("声音检索必须指定 format")
    if purpose == "voice" and query.strip():
        raise MemoryError("声音检索不接收主题 query；主题词只用于 novelty 查重")
    if purpose == "novelty" and not query.strip():
        raise MemoryError("查重检索必须提供 query 或 query-file")

    hits: list[SearchHit] = []
    normalized_query_hash = _text_hash(query) if query.strip() else ""
    for record in records:
        if format_name and record.format != format_name:
            continue
        if purpose == "voice":
            if not record.voice_eligible:
                continue
            if content_type and record.content_type != content_type:
                continue
        body = _body(library_root, record)
        if purpose == "voice":
            score = 0.0
            exact_text = False
        else:
            score = _coverage(query, (record.title, record.content_type)) * 8
            score += _coverage(query, (body,)) * 5
            if content_type:
                if record.content_type == content_type:
                    score += 6
                else:
                    score += _coverage(content_type, (record.content_type,)) * 2
            exact_text = normalized_query_hash == record.text_hash
            if score <= 0 and not exact_text:
                continue
        hits.append(
            SearchHit(
                record=record,
                score=score,
                exact_text=exact_text,
                opening=_excerpt(body),
                ending=_excerpt(body, from_end=True),
            )
        )

    if purpose == "voice":
        hits.sort(
            key=lambda hit: (hit.record.updated, hit.record.title),
            reverse=True,
        )
    else:
        hits.sort(
            key=lambda hit: (
                hit.exact_text,
                hit.score,
                hit.record.updated,
                hit.record.title,
            ),
            reverse=True,
        )
    return hits[:limit]


def render_search_results(
    hits: Sequence[SearchHit],
    *,
    purpose: str,
    memory_source: str,
    total: int,
    voice_total: int,
) -> str:
    if purpose == "voice":
        title = "作者声音候选"
        purpose_line = (
            "用途：只比较经过明确标注的声音证据。单篇中的具体句型、"
            "口头禅和转场不自动成为作者声音。"
        )
    else:
        title = "发布历史查重候选"
        purpose_line = (
            "用途：判断主题、主张、材料与旧内容是否重复；"
            "命中结果不提供作者声音。"
        )
    lines = [
        f"# {title}（{len(hits)} 条）",
        "",
        f"- 数据来源：{memory_source}",
        f"- 发布历史：{total} 条",
        f"- 可用声音证据：{voice_total} 条",
        f"- {purpose_line}",
        "",
    ]
    if not hits:
        empty = (
            "没有找到符合当前成品形态和内容职责的声音证据。"
            "继续使用当前用户语言与长期声音真源，不拿发布历史硬凑。"
            if purpose == "voice"
            else "没有找到相关旧内容。按当前材料继续，不制造重复判断。"
        )
        lines.extend([empty, ""])
    for index, hit in enumerate(hits, start=1):
        record = hit.record
        lines.extend(
            [
                f"## {index}. {record.title}",
                "",
                f"- 本地路径：{record.path}",
                f"- 成品形态：{record.format}",
                f"- 内容类型：{record.content_type or '未标注'}",
                f"- 发布归属：{record.publisher}",
                f"- 写作来源：{record.writing_origin}",
                f"- 声音资格：{'可用' if record.voice_eligible else '不可用'}",
                f"- 日期：{record.updated or '未标注'}",
            ]
        )
        if purpose == "novelty":
            lines.extend(
                [
                    f"- 相关度：{hit.score:.2f}",
                    f"- 完全同文：{'是' if hit.exact_text else '否'}",
                ]
            )
        if record.source_url:
            lines.append(f"- 发布入口：{record.source_url}")
        lines.extend(
            [
                "",
                "### 开头片段",
                "",
                hit.opening,
                "",
                "### 结尾片段",
                "",
                hit.ending,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _query_text(args: argparse.Namespace) -> str:
    if args.query:
        return args.query
    if not args.query_file:
        return ""
    path = Path(args.query_file).resolve()
    if not path.exists():
        raise MemoryError(f"查询文件不存在：{path}")
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8-sig"))
    return _normalize_text(body)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="维护发布历史，并分别检索查重记录与经过确认的声音证据"
    )
    parser.add_argument(
        "--library-root",
        type=Path,
        help="私人知识库根目录；省略时读取本机私人库配置",
    )
    parser.add_argument("--config", type=Path, help="本机私人库指针配置")
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-index", help="从正式成果和来源重建发布记录")
    build.add_argument(
        "--check",
        action="store_true",
        help="只检查现有索引是否与正文一致",
    )

    commands.add_parser("validate", help="检查正式来源与发布记录索引")

    search = commands.add_parser("search", help="按明确用途检索发布记录")
    search.add_argument(
        "--purpose",
        choices=sorted(SUPPORTED_SEARCH_PURPOSES),
        required=True,
    )
    query = search.add_mutually_exclusive_group(required=False)
    query.add_argument("--query", help="主题、主张、钩子或草稿")
    query.add_argument("--query-file", help="从 UTF-8 文件读取完整草稿")
    search.add_argument("--format", choices=sorted(SUPPORTED_FORMATS))
    search.add_argument("--content-type")
    search.add_argument("--limit", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        library_root = resolve_library_root(args.library_root, args.config)
        validate_library(library_root)
        current, receipt = discover_records(library_root)

        if args.command == "build-index":
            if args.check:
                if not index_is_current(library_root, current):
                    raise MemoryError("发布记录索引不存在或需要重建")
                print(
                    f"发布记录索引有效：{len(current)} 条；"
                    f"博客发布 {receipt.accepted_blog} 篇，"
                    f"确认成果 {receipt.accepted_outputs} 篇，"
                    f"社交发布 {receipt.accepted_social} 条。"
                )
                return 0
            index_path = write_index(library_root, current, args.config)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "index": str(index_path),
                        "records": len(current),
                        **asdict(receipt),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if args.command == "validate":
            if not index_is_current(library_root, current):
                raise MemoryError("发布记录索引不存在或与当前正文不一致")
            indexed = load_index(library_root)
            for record in indexed:
                _body(library_root, record)
            print(
                f"个人写作记忆有效：{len(indexed)} 条；"
                f"索引和正文一致，重复发布入口与同文已经合并。"
            )
            return 0

        if index_is_current(library_root, current):
            records = load_index(library_root)
            memory_source = "发布记录索引"
        else:
            records = current
            memory_source = "当前正式文件（索引未写入或需要更新）"
        query_text = _query_text(args)
        hits = search_memory(
            library_root=library_root,
            records=records,
            purpose=args.purpose,
            query=query_text,
            format_name=args.format,
            content_type=args.content_type,
            limit=args.limit,
        )
        print(
            render_search_results(
                hits,
                purpose=args.purpose,
                memory_source=memory_source,
                total=len(records),
                voice_total=sum(record.voice_eligible for record in records),
            ),
            end="",
        )
        return 0
    except (LibraryError, MemoryError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
