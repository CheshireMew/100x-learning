from __future__ import annotations

import json
import unittest

from scripts.normalize_subtitles import (
    Cue,
    merge_cues,
    normalize_cues,
    parse_subtitles,
    render_json,
    timestamp_to_seconds,
)


class SubtitleNormalizationTests(unittest.TestCase):
    def test_plain_text_never_gets_invented_timestamps(self) -> None:
        cues, source_format = parse_subtitles("第一段\n\n第二段")
        self.assertEqual("plain text", source_format)
        self.assertTrue(all(cue.start is None and cue.end is None for cue in cues))

    def test_invalid_clock_minutes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            timestamp_to_seconds("00:61:00")

    def test_end_before_start_is_rejected(self) -> None:
        subtitles = "00:10 --> 00:05\n错误时间\n"
        with self.assertRaises(ValueError):
            parse_subtitles(subtitles)

    def test_valid_srt_keeps_real_boundaries(self) -> None:
        subtitles = "1\n00:00:01,000 --> 00:00:03,500\nHello\n"
        cues, source_format = parse_subtitles(subtitles)
        self.assertEqual("SRT/VTT", source_format)
        self.assertEqual(1.0, cues[0].start)
        self.assertEqual(3.5, cues[0].end)

    def test_start_only_timestamps_do_not_invent_end_times(self) -> None:
        subtitles = "[00:01] 第一行\n[00:04] 第二行\n"
        cues, source_format = parse_subtitles(subtitles)

        self.assertEqual("timestamped text", source_format)
        self.assertEqual([1.0, 4.0], [cue.start for cue in cues])
        self.assertTrue(all(cue.end is None for cue in cues))

    def test_chinese_rolling_caption_overlap_is_removed_without_losing_new_text(self) -> None:
        cues = [
            Cue(1.0, 2.0, "Dropbox 自动同步所有文件"),
            Cue(2.0, 3.0, "自动同步所有文件覆盖你所有的设备"),
        ]

        merged = merge_cues(cues, max_gap=1.5, max_chars=280)

        self.assertEqual(1, len(merged))
        self.assertEqual(
            "Dropbox 自动同步所有文件 覆盖你所有的设备",
            merged[0].text,
        )
        self.assertEqual(1.0, merged[0].start)
        self.assertEqual(3.0, merged[0].end)

    def test_json_preserves_each_parsed_cue_for_agent_editing(self) -> None:
        cues = [Cue(1.0, 2.0, "第一句"), Cue(2.0, 3.0, "第二句")]

        payload = json.loads(render_json(cues, "SRT/VTT"))

        self.assertEqual(["第一句", "第二句"], [item["text"] for item in payload["segments"]])
        self.assertEqual([1.0, 2.0], [item["start"] for item in payload["segments"]])

    def test_normalized_cues_keep_timing_for_new_rolling_caption_text(self) -> None:
        cues = [
            Cue(1.0, 2.0, "桌面文件夹自动同步所有文件"),
            Cue(2.0, 3.0, "自动同步所有文件覆盖所有设备"),
        ]

        normalized = normalize_cues(cues)

        self.assertEqual(
            ["桌面文件夹自动同步所有文件", "覆盖所有设备"],
            [cue.text for cue in normalized],
        )
        self.assertEqual([(1.0, 2.0), (2.0, 3.0)], [(cue.start, cue.end) for cue in normalized])


if __name__ == "__main__":
    unittest.main()
