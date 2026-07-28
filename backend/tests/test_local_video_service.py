from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.services.local_video_service import LocalVideoService


class LocalVideoServiceTests(TestCase):
    def test_subtitles_cover_script(self) -> None:
        script = " ".join(f"word{index}" for index in range(1, 20))
        output = LocalVideoService._subtitles(script, 12.0)
        self.assertIn("00:00:00,000 -->", output)
        self.assertIn("word19", output)
        self.assertEqual(output.count("-->"), 3)

    def test_timestamp_format(self) -> None:
        self.assertEqual(
            LocalVideoService._timestamp(65.125),
            "00:01:05,125",
        )

    def test_voice_allowlist(self) -> None:
        LocalVideoService._validate_voice("af_heart")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            LocalVideoService._validate_voice("../../unsafe")
