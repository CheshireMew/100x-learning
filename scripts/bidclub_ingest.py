from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CATALOG_URL = "https://bidclub.ai/api/feed-index"
SHOWS_URL = "https://bidclub.ai/api/v1/shows"
DOWNLOAD_TEMPLATE = "https://bidclub.ai/dl/{slug}/full.md?lang=orig"

# These are the programmes whose primary editorial scope is investing, markets,
# macro, venture capital, or capital allocation. Their complete catalogues are
# in scope when --mode full is used.
WHOLE_SHOWS = {
    "1000x",
    "sohn",
    "shanghaojin",
    "gaonengliang",
    "iltb",
    "20vc",
    "allin",
    "sourcery",
}

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_TITLE_FILENAME_CHARS = 120

# A title match is intentionally stricter than a generic technology or company
# match. English matches also inspect BidClub's Chinese translated title.
DIRECT_TERMS = [
    "invest", "investor", "investing", "portfolio", "stock", "stocks",
    "equity", "venture capital", "private equity", "hedge fund",
    "fundraising", "fund raise", "valuation", "ipo", "m&a", "merger",
    "acquisition", "buyout", "bond", "bonds", "credit", "yield", "debt",
    "interest rate", "inflation", "recession", "gdp", "economy", "economic",
    "monetary", "fiscal", "federal reserve", "treasury", "currency",
    "commodit", "gold", "oil", "real estate", "housing", "wealth", "pension",
    "endowment", "family office", "sovereign wealth", "bitcoin", "crypto",
    "stablecoin", "tokenization", "earnings", "cash flow", "capital markets",
    "capital allocation", "private markets", "public markets", "liquidity",
    "risk asset", "risk assets", "trading",
    "投资", "投资人", "投资者", "投资逻辑", "投资札记", "基金", "风投",
    "创投", "融资", "估值", "上市", "并购", "债券", "债务", "利率",
    "通胀", "衰退", "经济", "宏观", "货币", "财政", "黄金", "石油",
    "房地产", "财富", "家族办公室", "比特币", "加密", "现金流", "资本市场",
    "资本流向", "价值投资", "二级市场", "一级市场", "一级半市场", "财报",
    "股市", "美股", "股票", "市场概述", "市场分析", "交易",
]


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "100x-learning BidClub ingestion/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, attempts: int = 4) -> str:
    request = Request(url, headers={"User-Agent": "100x-learning BidClub ingestion/1.0"})
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=120) as response:
                return response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if isinstance(error, HTTPError) and error.code not in {429, 500, 502, 503, 504}:
                raise
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    assert last_error is not None
    raise last_error


def matching_terms(episode: dict[str, Any]) -> list[str]:
    haystack = f"{episode.get('title') or ''} {episode.get('title_alt') or ''}".casefold()
    return [term for term in DIRECT_TERMS if term.casefold() in haystack]


def select_episodes(catalog: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for episode in catalog.get("episodes", []):
        reasons: list[str] = []
        if episode.get("show_id") in WHOLE_SHOWS:
            reasons.append("whole-show")
        terms = matching_terms(episode)
        if terms:
            reasons.append("title-match:" + ",".join(terms))
        if reasons:
            record = dict(episode)
            record["selection_reason"] = "; ".join(reasons)
            selected.append(record)

    if mode == "full":
        return selected

    # One recent representative from every whole-show scope plus a few
    # title-matched episodes outside those shows for the sample verification.
    sample: list[dict[str, Any]] = []
    for show_id in sorted(WHOLE_SHOWS):
        candidates = [e for e in selected if e.get("show_id") == show_id]
        if candidates:
            sample.append(candidates[0])
    outside = [e for e in selected if e.get("show_id") not in WHOLE_SHOWS]
    sample.extend(outside[:6])
    return sample


def yaml_string(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def render_document(episode: dict[str, Any], body: str) -> str:
    title = episode.get("title") or episode.get("slug")
    title_alt = episode.get("title_alt")
    show_name = episode.get("show_name") or episode.get("show_id")
    today = date.today().isoformat()
    metadata = [
        "---",
        "type: source-transcript",
        "status: active",
        f"created: {today}",
        f"updated: {today}",
        f"title: {yaml_string(title)}",
        f"title_zh: {yaml_string(title_alt)}",
        f"show: {yaml_string(show_name)}",
        f"show_id: {yaml_string(episode.get('show_id'))}",
        f"source_language: {yaml_string(episode.get('lang'))}",
        "transcript_language: source",
        f"date: {yaml_string(episode.get('date'))}",
        f"duration_min: {yaml_string(episode.get('duration_min'))}",
        f"source_url: {yaml_string(episode.get('source_url'))}",
        f"bidclub_url: {yaml_string('https://bidclub.ai/e/' + str(episode.get('slug')))}",
        f"download_url: {yaml_string(DOWNLOAD_TEMPLATE.format(slug=quote(str(episode.get('slug')), safe='')))}",
        f"selection: {yaml_string(episode.get('selection_reason'))}",
        "translation_status: not-translated",
        "---",
        "",
    ]
    return "\n".join(metadata) + body.rstrip() + "\n"


def safe_filename(episode: dict[str, Any]) -> str:
    raw_date = episode.get("date") or "undated"
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", str(episode.get("slug") or "episode"))
    return f"{raw_date}__{slug}.md"


def frontmatter_value(text: str, key: str) -> str:
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        return ""
    field = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", match.group(1))
    if not field:
        return ""
    raw = field.group(1)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw.strip('"')
    return "" if value is None else str(value)


def filename_title(text: str) -> str:
    language = frontmatter_value(text, "source_language").upper()
    primary = frontmatter_value(text, "title")
    alternate = frontmatter_value(text, "title_zh")
    if language == "ZH":
        return primary or alternate or "未命名单集"
    return alternate or primary or "未命名单集"


def sanitize_title_for_filename(title: str) -> str:
    value = unicodedata.normalize("NFKC", title).strip()
    value = re.sub(r"[\x00-\x1f\x7f]", "-", value)
    value = re.sub(r'[<>:"/\\|?*]', "-", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"-{2,}", "-", value)
    value = value.rstrip(" .")
    if not value:
        value = "未命名单集"
    if value.upper() in WINDOWS_RESERVED_NAMES:
        value = "_" + value
    if len(value) > MAX_TITLE_FILENAME_CHARS:
        digest = __import__("hashlib").sha1(value.encode("utf-8")).hexdigest()[:8]
        keep = MAX_TITLE_FILENAME_CHARS - len(digest) - 1
        value = value[:keep].rstrip(" .-") + "-" + digest
    return value


def path_key(path: Path) -> str:
    return str(path.absolute()).casefold()


def build_rename_plan(destination: Path) -> tuple[list[tuple[Path, Path]], int, int]:
    source_files = sorted(destination.rglob("*.md"), key=lambda path: path_key(path))
    entries: list[tuple[Path, str, str]] = []
    source_keys: set[str] = set()
    for path in source_files:
        text = path.read_text(encoding="utf-8-sig")
        if frontmatter_value(text, "type") != "source-transcript":
            continue
        source_keys.add(path_key(path))
        raw_date = frontmatter_value(text, "date") or "undated"
        safe_date = re.sub(r"[^A-Za-z0-9_-]+", "-", raw_date).strip("-_") or "undated"
        title = sanitize_title_for_filename(filename_title(text))
        entries.append((path, safe_date, title))

    reserved_non_source = {
        path_key(path) for path in source_files if path_key(path) not in source_keys
    }
    used_targets: set[str] = set()
    plan: list[tuple[Path, Path]] = []
    collision_count = 0
    for source, raw_date, title in entries:
        suffix_number = 1
        while True:
            suffix = "" if suffix_number == 1 else f"__{suffix_number}"
            candidate = source.parent / f"{raw_date}__{title}{suffix}.md"
            candidate_key = path_key(candidate)
            if candidate_key not in used_targets and candidate_key not in reserved_non_source:
                break
            suffix_number += 1
        if suffix_number > 1:
            collision_count += 1
        used_targets.add(candidate_key)
        plan.append((source, candidate))

    return plan, collision_count, len(entries)


def rename_documents(destination: Path, dry_run: bool) -> dict[str, Any]:
    plan, collision_count, source_count = build_rename_plan(destination)
    changes = [(source, target) for source, target in plan if path_key(source) != path_key(target)]
    if not dry_run and changes:
        moved_to_temp: list[tuple[Path, Path]] = []
        completed: list[tuple[Path, Path]] = []
        try:
            for index, (source, _target) in enumerate(changes):
                temporary = source.with_name(f".__bidclub_rename_{index}.tmp")
                if temporary.exists():
                    raise FileExistsError(f"temporary rename path already exists: {temporary}")
                source.replace(temporary)
                moved_to_temp.append((temporary, source))
            for temporary, target in zip(
                (item[0] for item in moved_to_temp),
                (item[1] for item in changes),
            ):
                temporary.replace(target)
                completed.append((target, temporary))
        except Exception:
            for target, temporary in reversed(completed):
                if target.exists():
                    target.replace(temporary)
            for temporary, source in reversed(moved_to_temp):
                if temporary.exists():
                    temporary.replace(source)
            raise

    return {
        "mode": "rename",
        "dry_run": dry_run,
        "source_count": source_count,
        "changed_count": len(changes),
        "unchanged_count": source_count - len(changes),
        "collision_count": collision_count,
        "examples": [
            {"from": str(source), "to": str(target)}
            for source, target in changes[:10]
        ],
    }


def download_one(episode: dict[str, Any], root: Path) -> dict[str, Any]:
    show_dir = root / str(episode.get("show_id") or "unknown")
    show_dir.mkdir(parents=True, exist_ok=True)
    target = show_dir / safe_filename(episode)
    if target.exists() and target.stat().st_size > 0:
        return {"slug": episode.get("slug"), "status": "skipped-existing", "path": str(target)}

    slug = quote(str(episode.get("slug")), safe="")
    url = DOWNLOAD_TEMPLATE.format(slug=slug)
    body = fetch_text(url)
    if not body.strip():
        raise RuntimeError(f"empty response for {episode.get('slug')}")
    target.write_text(render_document(episode, body), encoding="utf-8", newline="\n")
    return {"slug": episode.get("slug"), "status": "downloaded", "path": str(target), "chars": len(body)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest BidClub investment transcripts into the 100x-learning source library.")
    parser.add_argument("--library-root", required=True, type=Path)
    parser.add_argument("--mode", choices=["sample", "full", "rename"], default="sample")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    destination = args.library_root / "20-Sources" / "Transcripts" / "BidClub"
    if args.mode == "rename":
        if not destination.exists():
            raise FileNotFoundError(f"BidClub transcript directory does not exist: {destination}")
        print(json.dumps(rename_documents(destination, args.dry_run), ensure_ascii=False, indent=2))
        return 0

    catalog = fetch_json(CATALOG_URL)
    shows_payload = fetch_json(SHOWS_URL)
    show_names = {show.get("id"): show.get("name") for show in shows_payload.get("shows", [])}
    selected = select_episodes(catalog, args.mode)
    for episode in selected:
        episode["show_name"] = show_names.get(episode.get("show_id"), episode.get("show_id"))

    if args.dry_run:
        by_show: dict[str, int] = {}
        for episode in selected:
            by_show[str(episode.get("show_id"))] = by_show.get(str(episode.get("show_id")), 0) + 1
        print(json.dumps({
            "mode": args.mode,
            "catalog_count": catalog.get("count"),
            "selected_count": len(selected),
            "selected_by_show": dict(sorted(by_show.items())),
        }, ensure_ascii=False, indent=2))
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(download_one, episode, destination): episode for episode in selected}
        for future in concurrent.futures.as_completed(futures):
            episode = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as error:  # keep the batch resumable
                failures.append({"slug": episode.get("slug"), "error": repr(error)})

    by_show: dict[str, int] = {}
    for episode in selected:
        by_show[str(episode.get("show_id"))] = by_show.get(str(episode.get("show_id")), 0) + 1
    summary = {
        "mode": args.mode,
        "catalog_count": catalog.get("count"),
        "selected_count": len(selected),
        "downloaded_count": sum(r.get("status") == "downloaded" for r in results),
        "skipped_existing_count": sum(r.get("status") == "skipped-existing" for r in results),
        "failure_count": len(failures),
        "selected_by_show": dict(sorted(by_show.items())),
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
