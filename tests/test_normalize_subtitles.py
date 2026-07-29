from __future__ import annotations

import unittest

from scripts.normalize_subtitles import parse_subtitles, timestamp_to_seconds


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


if __name__ == "__main__":
    unittest.main()
