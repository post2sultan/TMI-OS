import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.services.local_video_service import LocalVideoService


class LocalVideoServiceTests(TestCase):
    def test_subtitles_cover_script(self) -> None:
        script = " ".join(f"word{index}" for index in range(1, 20))
        output = LocalVideoService._subtitles(script, 12.0)
        self.assertIn("00:00:00,000 -->", output)
        self.assertIn("word19", output)
        self.assertEqual(output.count("-->"), 3)
        self.assertIn("word1 word2 word3 word4 word5 word6 word7\n", output)

    def test_timestamp_format(self) -> None:
        self.assertEqual(
            LocalVideoService._timestamp(65.125),
            "00:01:05,125",
        )

    def test_voice_allowlist(self) -> None:
        LocalVideoService._validate_voice("af_heart")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            LocalVideoService._validate_voice("../../unsafe")

    def test_render_retries_without_stock_and_replaces_output_atomically(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory)
            stock = target / "stock.mp4"
            audio = target / "voiceover.wav"
            subtitles = target / "captions.srt"
            logo = target / "logo.png"
            output = target / "video.mp4"
            for path in (stock, audio, subtitles, logo):
                path.write_bytes(b"source")
            output.write_bytes(b"previous-video")

            def run(command, **_kwargs):
                destination = Path(command[-1])
                if destination.name.startswith("clip-"):
                    destination.write_bytes(b"c" * 10_001)
                    return None
                if "concat" in command:
                    destination.write_bytes(b"partial")
                    raise subprocess.CalledProcessError(187, command)
                destination.write_bytes(b"v" * 10_001)
                return None

            with patch("app.services.local_video_service.subprocess.run", side_effect=run):
                LocalVideoService._render(
                    [stock], audio, subtitles, logo, output, 1080, 1920, 5.0
                )

            self.assertEqual(output.stat().st_size, 10_001)
            self.assertFalse((target / "video.tmp.mp4").exists())
