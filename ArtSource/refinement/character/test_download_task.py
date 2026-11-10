"""Offline regressions for successful-task artifact downloads."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import download_task as downloader


class Response(io.BytesIO):
    def __init__(self, body, status, headers):
        super().__init__(body)
        self.status = status
        self.headers = headers


def glb_fixture():
    document = json.dumps({"asset": {"version": "2.0"},
                           "buffers": [{"byteLength": 16}]}).encode()
    document += b" " * (-len(document) % 4)
    binary = bytes(range(16))
    length = 12 + 8 + len(document) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, length)
            + struct.pack("<II", len(document), 0x4E4F534A) + document
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


class DownloadTaskTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.task_path = self.directory / "response.json"
        self.output = self.directory / "artifacts"
        self.task = {
            "task_id": "offline-retarget", "type": "retarget", "status": "success",
            "input": {"animation": "preset:slash", "model_version": "v3.0"},
            "credits_consumed": 10,
            "output": {"model_url": "https://example.test/model.glb?Signature=hidden"},
        }
        self.argv = ["download_task.py", self.task["task_id"],
                     "--task-json", str(self.task_path), "--output", str(self.output)]

    def test_model_only_download_and_verified_repeat_skip(self):
        model = glb_fixture()
        self.task_path.write_text(json.dumps(self.task))

        def serve(url, method="GET", headers=None):
            self.assertEqual(url, self.task["output"]["model_url"])
            if method == "HEAD":
                return Response(b"", 200, {"Content-Length": str(len(model)),
                                            "Accept-Ranges": "bytes", "ETag": '"fixture"'})
            self.assertEqual(method, "GET")
            start, end = map(int, headers["Range"].removeprefix("bytes=").split("-"))
            return Response(model[start:end + 1], 206,
                            {"Content-Range": f"bytes {start}-{end}/{len(model)}",
                             "Content-Length": str(end - start + 1), "ETag": '"fixture"'})

        with patch.object(downloader, "open_url", side_effect=serve) as http, \
                patch.object(downloader.subprocess, "run", side_effect=AssertionError("Unexpected task query")) as query, \
                patch.object(sys, "argv", self.argv), redirect_stdout(io.StringIO()):
            downloader.main()
            self.assertEqual(http.call_count, 5)  # One HEAD and four Range requests.
            self.assertEqual((self.output / "model.glb").read_bytes(), model)
            receipt = json.loads((self.output / "download_receipt.json").read_text())
            metadata_text = (self.output / "task.json").read_text()
            metadata = json.loads(metadata_text)
            self.assertIsNone(metadata["artifacts"]["preview"])
            self.assertIsNone(receipt["preview"])
            self.assertEqual(receipt["workers"], 4)
            self.assertEqual(receipt["model"]["bytes"], len(model))
            self.assertEqual(receipt["model"]["glb_declared_bytes"], len(model))
            self.assertEqual(receipt["model"]["sha256"], hashlib.sha256(model).hexdigest())
            self.assertNotIn("Signature", metadata_text)
            self.assertFalse(list(self.output.glob("preview*")))
            self.assertFalse((self.output / ".parts").exists())

            http.reset_mock()
            http.side_effect = AssertionError("Unexpected repeat HTTP request")
            downloader.main()
            http.assert_not_called()
            query.assert_not_called()

    def test_short_206_resumes_only_missing_tail(self):
        payload = bytes(range(100))
        requested = []

        def serve(url, method="GET", headers=None):
            requested.append(headers["Range"])
            if len(requested) == 1:
                return Response(payload[:60], 206,
                                {"Content-Range": "bytes 0-99/100", "Content-Length": "100"})
            return Response(payload[60:], 206,
                            {"Content-Range": "bytes 60-99/100", "Content-Length": "40"})

        with patch.object(downloader, "open_url", side_effect=serve), \
                patch.object(downloader.time, "sleep"), redirect_stdout(io.StringIO()):
            downloader.download_part("https://example.test/model.glb", self.directory,
                                     0, 0, 99, 100, None)
        self.assertEqual(requested, ["bytes=0-99", "bytes=60-99"])
        self.assertEqual((self.directory / "00.part").read_bytes(), payload)

    def test_invalid_task_artifacts_are_rejected_before_download(self):
        cases = (
            {"status": "running", "output": self.task["output"]},
            {"status": "success", "output": {}},
            {"status": "success", "output": {
                "model_url": "https://example.test/model.glb",
                "rendered_image_url": "http://example.test/preview.webp"}},
        )
        with patch.object(downloader, "open_url") as http, \
                patch.object(downloader.subprocess, "run") as query:
            for case in cases:
                with self.subTest(case=case):
                    task = dict(self.task)
                    task.update(case)
                    self.task_path.write_text(json.dumps(task))
                    args = SimpleNamespace(task_id=self.task["task_id"], task_json=self.task_path)
                    with self.assertRaises(downloader.DownloadError):
                        downloader.task_response(args)
            http.assert_not_called()
            query.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_saved_ranges_reject_gap_and_overlap(self):
        downloader.validate_ranges([[0, 4], [5, 9]], 10)
        for ranges in ([[0, 3], [5, 9]], [[0, 5], [5, 9]]):
            with self.subTest(ranges=ranges), self.assertRaises(downloader.DownloadError):
                downloader.validate_ranges(ranges, 10)


if __name__ == "__main__":
    unittest.main()
