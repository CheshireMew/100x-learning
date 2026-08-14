#!/usr/bin/env python3
"""Normalize SRT, VTT, or timestamped transcripts without inventing timing."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TIMING_RE = re.compile(
    r"^\s*(?P<start>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)"
    r"\s*-->\s*"
    r"(?P<end>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)"
)
PREFIXED_RE = re.compile(
    r"^\s*\[?(?P<start>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\]?"
    r"\s*(?:[-–—]\s*)?(?P<text>\S.*)$"
)
TIMESTAMP_ONLY_RE = re.compile(
    r"^\s*\[?(?P<start>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\]?\s*$"
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
SENTENCE_END_RE = re.compile(r"[。！？!?；;.]\s*[\"'”’）)]*$")


@dataclass
class Cue:
    start: float | None
    end: float | None
    text: str


def timestamp_to_seconds(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours = "0"
            minutes, seconds = parts
        else:
            raise ValueError
        hours_value = int(hours)
        minutes_value = int(minutes)
        seconds_value = float(seconds)
        if hours_value < 0 or not 0 <= minutes_value < 60 or not 0 <= seconds_value < 60:
            raise ValueError
        return hours_value * 3600 + minutes_value * 60 + seconds_value
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value}") from exc


def format_timestamp(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    if hours:
        base = f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}"
    else:
        base = f"{minutes:02d}:{whole_seconds:02d}"
    return f"{base}.{millis:03d}" if millis else base


def clean_text(value: str) -> str:
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return SPACE_RE.sub(" ", value).strip()


def remove_overlap(previous: str, current: str) -> str:
    """Remove repeated words caused by rolling automatic captions."""
    if not previous or not current:
        return current
    if current == previous or current in previous:
        return ""
    if previous in current:
        return current[len(previous) :].lstrip(" ,，。")

    previous_words = previous.split()
    current_words = current.split()
    max_overlap = min(len(previous_words), len(current_words), 12)
    for size in range(max_overlap, 1, -1):
        if previous_words[-size:] == current_words[:size]:
            return " ".join(current_words[size:])
    return current


def parse_cued_text(lines: list[str]) -> list[Cue]:
    cues: list[Cue] = []
    index = 0
    while index < len(lines):
        timing = TIMING_RE.match(lines[index])
        if not timing:
            index += 1
            continue

        start = timestamp_to_seconds(timing.group("start"))
        end = timestamp_to_seconds(timing.group("end"))
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and not TIMING_RE.match(lines[index]):
            line = lines[index].strip()
            if line and not line.isdigit() and not line.startswith(("NOTE", "STYLE", "REGION")):
                text_lines.append(line)
            index += 1
        text = clean_text(" ".join(text_lines))
        if text:
            cues.append(Cue(start, end, text))
    return cues


def parse_timestamped_lines(lines: list[str]) -> list[Cue]:
    cues: list[Cue] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        prefixed = PREFIXED_RE.match(line)
        if prefixed:
            cues.append(
                Cue(
                    timestamp_to_seconds(prefixed.group("start")),
                    None,
                    clean_text(prefixed.group("text")),
                )
            )
            index += 1
            continue

        timestamp_only = TIMESTAMP_ONLY_RE.match(line)
        if timestamp_only:
            start = timestamp_to_seconds(timestamp_only.group("start"))
            index += 1
            text_lines: list[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                if TIMESTAMP_ONLY_RE.match(candidate) or PREFIXED_RE.match(candidate):
                    break
                if candidate:
                    text_lines.append(candidate)
                index += 1
            text = clean_text(" ".join(text_lines))
            if text:
                cues.append(Cue(start, None, text))
            continue
        index += 1

    for cue_index, cue in enumerate(cues[:-1]):
        if cue.end is None:
            cue.end = cues[cue_index + 1].start
    return cues


def parse_plain_text(text: str) -> list[Cue]:
    paragraphs = re.split(r"\n\s*\n", text.strip())
    if len(paragraphs) == 1:
        paragraphs = [line for line in text.splitlines() if line.strip()]
    return [Cue(None, None, clean_text(paragraph)) for paragraph in paragraphs if clean_text(paragraph)]


def validate_cues(cues: list[Cue]) -> None:
    previous_start: float | None = None
    for index, cue in enumerate(cues, start=1):
        if cue.start is not None and previous_start is not None and cue.start < previous_start:
            raise ValueError(f"timestamps are not monotonic at cue {index}")
        if cue.start is not None:
            previous_start = cue.start
        if cue.start is not None and cue.end is not None and cue.end < cue.start:
            raise ValueError(f"end timestamp precedes start at cue {index}")


def parse_subtitles(text: str) -> tuple[list[Cue], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = normalized.splitlines()
    if any(TIMING_RE.match(line) for line in lines):
        source_format = "VTT" if normalized.lstrip().startswith("WEBVTT") else "SRT/VTT"
        cues = parse_cued_text(lines)
        validate_cues(cues)
        return cues, source_format

    timestamped = parse_timestamped_lines(lines)
    if timestamped:
        validate_cues(timestamped)
        return timestamped, "timestamped text"
    cues = parse_plain_text(normalized)
    validate_cues(cues)
    return cues, "plain text"


def merge_cues(cues: list[Cue], max_gap: float, max_chars: int) -> list[Cue]:
    merged: list[Cue] = []
    current: Cue | None = None

    for cue in cues:
        text = clean_text(cue.text)
        if not text:
            continue
        if current is None:
            current = Cue(cue.start, cue.end, text)
            continue

        addition = remove_overlap(current.text, text)
        if not addition:
            current.end = cue.end
            continue

        timed = current.end is not None and cue.start is not None
        gap = cue.start - current.end if timed else 0.0
        ends_sentence = bool(SENTENCE_END_RE.search(current.text))
        too_long = len(current.text) + 1 + len(addition) > max_chars
        discontinuous = timed and gap > max_gap

        if too_long or discontinuous or (ends_sentence and len(current.text) >= 40):
            merged.append(current)
            current = Cue(cue.start, cue.end, text)
        else:
            separator = "" if current.text.endswith((" ", "，", ",")) else " "
            current.text = clean_text(current.text + separator + addition)
            current.end = cue.end

    if current is not None:
        merged.append(current)
    return merged


def render_markdown(cues: list[Cue], source_format: str) -> str:
    lines = ["# 规范化字幕", "", f"来源格式：{source_format}", ""]
    for index, cue in enumerate(cues, start=1):
        start = format_timestamp(cue.start)
        end = format_timestamp(cue.end)
        if start and end and end != start:
            location = f"{start}–{end}"
        elif start:
            location = start
        else:
            location = f"片段 {index}"
        lines.append(f"- [{location}] {cue.text}")
    return "\n".join(lines) + "\n"


def render_json(cues: list[Cue], source_format: str) -> str:
    payload = {
        "source_format": source_format,
        "segments": [
            {
                **asdict(cue),
                "start_display": format_timestamp(cue.start),
                "end_display": format_timestamp(cue.end),
            }
            for cue in cues
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize subtitle timing and merge broken caption lines."
    )
    parser.add_argument("input", help="SRT/VTT/TXT file path, or - for stdin")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-gap", type=float, default=1.5, help="maximum merge gap in seconds")
    parser.add_argument("--max-chars", type=int, default=280, help="maximum merged segment length")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_gap < 0 or args.max_chars < 40:
        print("error: --max-gap must be non-negative and --max-chars at least 40", file=sys.stderr)
        return 2
    try:
        text = read_input(args.input)
        cues, source_format = parse_subtitles(text)
        if not cues:
            raise ValueError("no subtitle text found")
        merged = (
            cues
            if source_format == "plain text"
            else merge_cues(cues, args.max_gap, args.max_chars)
        )
        output = (
            render_json(merged, source_format)
            if args.format == "json"
            else render_markdown(merged, source_format)
        )
        sys.stdout.write(output)
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
