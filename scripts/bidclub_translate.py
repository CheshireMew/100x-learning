from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import time
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
DEFAULT_CHUNK_CHARS = 18_000

SYSTEM_PROMPT = """你是专业的英文播客全文翻译者，负责把输入的英文 Markdown 播客稿完整翻译成自然、准确、易读的简体中文。

严格遵守以下要求：
1. 只输出译文，不要解释翻译过程，不要加“译文如下”等开场白。
2. 完整翻译，不摘要、不删减、不补写，不改变事实、数字、人物关系、观点、限定条件、例子、重复和说话顺序。
3. 保留 Markdown 结构：标题层级、项目符号、粗体、斜体、引用、段落和说话人标签都要保留。标题和摘要正文翻译成中文。
4. 保留所有 URL、代码、代码片段、股票代码、产品名、公司名和专有名词的可识别性。人名、机构和产品优先使用自然的中文译法；没有稳定中文译法时保留英文原名。不要为了说明译法自行添加括号内容。
5. 保留原文的语气、口语表达、犹豫、自我修正和重复，不把访谈改写成总结或文章。
6. 输入中的特殊占位符（例如 __URL_0__、__CODE_0__）必须原样保留，不能翻译、删除或改写。
7. 如果输入在句子中间开始或结束，按当前片段忠实翻译，不要补齐前后片段没有提供的内容。
"""


class TranslationError(RuntimeError):
    pass


def parse_env_file(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise TranslationError(f"无法读取本地配置：{path}") from exc
    values: dict[str, str] = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[name.strip()] = value
    return values


def resolve_api_key(env_file: Path) -> str:
    environment_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if environment_key:
        return environment_key
    key = parse_env_file(env_file).get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise TranslationError(f"本地配置缺少 DEEPSEEK_API_KEY：{env_file}")
    return key


def request_json(
    *,
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
    attempts: int = 5,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(
            f"{BASE_URL}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise TranslationError("DeepSeek API 返回的顶层数据不是对象")
            return value
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            last_error = TranslationError(
                f"DeepSeek API 返回 HTTP {exc.code}：{response_body[:500]}"
            )
            if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                raise last_error from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(min(30, 2 ** attempt))
    raise TranslationError(f"DeepSeek API 请求失败：{last_error}") from last_error


def frontmatter(text: str) -> str:
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        raise TranslationError("来源文件缺少有效 frontmatter")
    return match.group(1)


def frontmatter_value(text: str, key: str) -> str:
    field = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", frontmatter(text))
    if not field:
        return ""
    raw = field.group(1)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw.strip('"')
    return "" if value is None else str(value)


def body_of(text: str) -> str:
    match = re.match(r"^---\r?\n.*?\r?\n---\s*\r?\n(.*)$", text, re.DOTALL)
    if not match:
        raise TranslationError("来源文件缺少正文")
    return match.group(1).strip()


def protect_patterns(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}

    def replace(match: re.Match[str], prefix: str) -> str:
        token = f"__{prefix}_{len(protected)}__"
        protected[token] = match.group(0)
        return token

    text = re.sub(r"https?://[^\s)\]>]+", lambda m: replace(m, "URL"), text)
    text = re.sub(r"```[\s\S]*?```", lambda m: replace(m, "CODE"), text)
    text = re.sub(r"`[^`\n]+`", lambda m: replace(m, "CODE"), text)
    return text, protected


def restore_patterns(text: str, protected: dict[str, str]) -> str:
    for token, value in protected.items():
        if token not in text:
            raise TranslationError(f"译文丢失占位符：{token}")
        text = text.replace(token, value)
    return text


def split_long_unit(unit: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    remaining = unit
    while len(remaining) > max_chars:
        cut = remaining.rfind("\n", 0, max_chars)
        if cut < max_chars // 2:
            cut = remaining.rfind(" ", 0, max_chars)
        if cut < max_chars // 2:
            cut = max_chars
        pieces.append(remaining[:cut])
        remaining = remaining[cut:]
    if remaining:
        pieces.append(remaining)
    return pieces


def make_chunks(text: str, max_chars: int) -> list[str]:
    units = re.split(r"\n\s*\n", text)
    expanded: list[str] = []
    for unit in units:
        expanded.extend(split_long_unit(unit, max_chars))
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for unit in expanded:
        extra = len(unit) if not current else len(unit) + 2
        if current and current_length + extra > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_length = 0
        current.append(unit)
        current_length += len(unit) if len(current) == 1 else len(unit) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [""]


def translate_chunk(
    text: str,
    *,
    api_key: str,
    max_tokens: int,
    timeout: int,
) -> str:
    protected_text, protected = protect_patterns(text)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": protected_text},
        ],
        "max_tokens": max_tokens,
        "stream": False,
    }
    response = request_json(
        api_key=api_key,
        payload=payload,
        timeout=timeout,
    )
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise TranslationError("DeepSeek 响应缺少 choices")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise TranslationError("DeepSeek choices[0] 不是对象")
    if choice.get("finish_reason") != "stop":
        raise TranslationError(
            f"DeepSeek 未完整生成当前片段，finish_reason={choice.get('finish_reason')!r}"
        )
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise TranslationError("DeepSeek 响应没有可交付译文")
    return restore_patterns(content.strip(), protected)


def translated_title(text: str) -> str:
    return frontmatter_value(text, "title_zh") or frontmatter_value(text, "title")


def replace_first_heading(body: str, title: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            lines[index] = f"# {title}"
            break
    return "\n".join(lines)


def yaml_string(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def render_translation(source_text: str, translated_body: str, source_path: Path, library_root: Path) -> str:
    source_relative = source_path.relative_to(library_root).as_posix()
    original_title = frontmatter_value(source_text, "title")
    title_zh = translated_title(source_text)
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    metadata = [
        "---",
        "type: source-transcript-translation",
        "status: active",
        f"created: {date.today().isoformat()}",
        f"updated: {date.today().isoformat()}",
        f"title: {yaml_string(title_zh)}",
        f"title_original: {yaml_string(original_title)}",
        f"show: {yaml_string(frontmatter_value(source_text, 'show'))}",
        f"show_id: {yaml_string(frontmatter_value(source_text, 'show_id'))}",
        "source_language: \"EN\"",
        "transcript_language: \"zh-CN\"",
        f"date: {yaml_string(frontmatter_value(source_text, 'date'))}",
        f"duration_min: {yaml_string(frontmatter_value(source_text, 'duration_min'))}",
        f"source_url: {yaml_string(frontmatter_value(source_text, 'source_url'))}",
        f"bidclub_url: {yaml_string(frontmatter_value(source_text, 'bidclub_url'))}",
        f"download_url: {yaml_string(frontmatter_value(source_text, 'download_url'))}",
        f"source_path: {yaml_string(source_relative)}",
        f"source_file_sha256: {yaml_string(source_hash)}",
        "translation_status: translated",
        "translation_provider: DeepSeek",
        f"translation_model: {MODEL}",
        "---",
        "",
    ]
    return "\n".join(metadata) + replace_first_heading(translated_body, title_zh).rstrip() + "\n"


def translate_file(
    source_path: Path,
    destination_root: Path,
    library_root: Path,
    *,
    api_key: str,
    max_tokens: int,
    timeout: int,
    chunk_chars: int,
    force: bool,
) -> dict[str, Any]:
    source_text = source_path.read_text(encoding="utf-8-sig")
    if frontmatter_value(source_text, "source_language").upper() != "EN":
        return {"status": "skipped-non-english", "source": str(source_path)}
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    relative = source_path.relative_to(library_root / "20-Sources" / "Transcripts" / "BidClub")
    target = destination_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        existing = target.read_text(encoding="utf-8-sig")
        if frontmatter_value(existing, "source_file_sha256") == source_hash:
            return {"status": "skipped-existing", "source": str(source_path), "target": str(target)}

    body = body_of(source_text)
    chunks = make_chunks(body, chunk_chars)
    translated_parts = [
        translate_chunk(
            chunk,
            api_key=api_key,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        for chunk in chunks
    ]
    translated_body = "\n\n".join(translated_parts)
    target.write_text(
        render_translation(source_text, translated_body, source_path, library_root),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "status": "translated",
        "source": str(source_path),
        "target": str(target),
        "chunks": len(chunks),
        "source_chars": len(body),
        "translated_chars": len(translated_body),
    }


def select_sources(source_root: Path, mode: str, limit: int) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source_root.rglob("*.md"), key=lambda item: str(item).casefold()):
        if "Translated" in path.relative_to(source_root).parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if frontmatter_value(text, "source_language").upper() == "EN":
            files.append(path)
    if mode == "full":
        return files
    if not files:
        return []
    count = max(1, min(limit, len(files)))
    if count == 1:
        return [files[len(files) // 2]]
    indexes = {0, len(files) // 2, len(files) - 1}
    if count > 3:
        indexes.update(round(i * (len(files) - 1) / (count - 1)) for i in range(count))
    return [files[index] for index in sorted(indexes)][:count]


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate BidClub English source transcripts into Chinese companions.")
    parser.add_argument("--library-root", required=True, type=Path)
    parser.add_argument("--mode", choices=["sample", "full"], default="sample")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    library_root = args.library_root.resolve()
    source_root = library_root / "20-Sources" / "Transcripts" / "BidClub"
    destination_root = source_root / "Translated"
    sources = select_sources(source_root, args.mode, args.limit)
    if args.dry_run:
        print(json.dumps({
            "mode": args.mode,
            "source_count": len(sources),
            "source_chars": sum(len(body_of(path.read_text(encoding="utf-8-sig"))) for path in sources),
            "sources": [str(path) for path in sources],
        }, ensure_ascii=False, indent=2))
        return 0

    api_key = resolve_api_key(args.env_file)
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(
                translate_file,
                source,
                destination_root,
                library_root,
                api_key=api_key,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                chunk_chars=args.chunk_chars,
                force=args.force,
            ): source
            for source in sources
        }
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            source = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(f"[progress] {index}/{len(sources)} {result.get('status')} {source.name}", flush=True)
            except Exception as error:
                failures.append({"source": str(source), "error": repr(error)})
                print(f"[failure] {index}/{len(sources)} {source.name}: {error}", flush=True)

    summary = {
        "mode": args.mode,
        "source_count": len(sources),
        "translated_count": sum(result.get("status") == "translated" for result in results),
        "skipped_existing_count": sum(result.get("status") == "skipped-existing" for result in results),
        "failure_count": len(failures),
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
