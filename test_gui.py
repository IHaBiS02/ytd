"""Headless integration checks: QT_QPA_PLATFORM=offscreen python3 -m unittest."""

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication

import gui


class DownloadWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.window = gui.DownloadWindow()
        self.window.kill_timer.setInterval(100)

    def tearDown(self):
        if self.window.active:
            self.window.stop_download()
            self.wait_for(lambda: not self.window.active)
        self.window.close()
        self.directory.cleanup()

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertTrue(predicate(), self.window.log.toPlainText())

    def start_worker(self, body):
        (self.root / "yt-dlp.sh").write_text(body, encoding="utf-8")
        self.window.url.setText("https://example.com/watch?v=test&list=one")
        with patch.object(gui, "__file__", str(self.root / "gui.py")):
            self.window.start_download()

    def test_live_logs_stderr_and_success(self):
        self.start_worker(
            'printf "준비 중\\n"; printf "%s\\n" "$1"; '
            'printf "진단 메시지\\n" >&2; sleep 0.3; printf "완료\\n"'
        )
        self.wait_for(lambda: "준비 중" in self.window.log.toPlainText())
        self.assertTrue(self.window.active)
        self.wait_for(lambda: not self.window.active)
        self.assertIn("진단 메시지", self.window.log.toPlainText())
        self.assertIn("https://example.com/watch?v=test&list=one", self.window.log.toPlainText())
        self.assertIn("완료", self.window.status.text())
        self.assertTrue(self.window.start_button.isEnabled())

    def test_error_is_retained_and_can_retry(self):
        self.start_worker('printf "다운로드 오류\\n" >&2; exit 7')
        self.wait_for(lambda: not self.window.active)
        self.assertIn("실패", self.window.status.text())
        self.assertIn("7", self.window.status.text())
        self.assertIn("다운로드 오류", self.window.log.toPlainText())
        self.start_worker('printf "재시도 성공\\n"')
        self.wait_for(lambda: not self.window.active)
        self.assertIn("완료", self.window.status.text())

    def test_invalid_url_does_not_start(self):
        self.window.url.setText("not a URL")
        self.window.start_download()
        self.assertFalse(self.window.active)
        self.assertEqual(self.window.process.state(), QProcess.ProcessState.NotRunning)

    def test_close_stops_descendants_even_if_they_ignore_term(self):
        self.start_worker(
            "bash -c 'trap \"\" TERM; echo child-ready; while :; do sleep 1; done' &\n"
            'wait\n'
        )
        self.wait_for(lambda: "child-ready" in self.window.log.toPlainText())
        group_id = self.window.group_id
        self.window.close()
        self.wait_for(lambda: not self.window.active)
        self.assertIn("중단", self.window.status.text())
        # Orphaned zombies may briefly remain until init reaps them; none may run.
        running = []
        for stat in Path("/proc").glob("[0-9]*/stat"):
            try:
                fields = stat.read_text().rsplit(")", 1)[1].split()
                if int(fields[2]) == group_id and fields[0] != "Z":
                    running.append(stat.parent.name)
            except (OSError, ValueError):
                continue
        self.assertEqual(running, [])

    def test_chosen_folder_is_saved_and_passed_to_worker(self):
        chosen = str(self.root / "저장 폴더")
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "config")}), \
                patch.object(gui.QFileDialog, "getExistingDirectory", return_value=chosen):
            self.window.choose_folder()
            self.assertEqual(str(gui.download_base()), chosen)
        self.start_worker('printf "폴더=%s\\n" "$YTD_DOWNLOAD_DIR"')
        self.wait_for(lambda: not self.window.active)
        self.assertIn(f"폴더={chosen}", self.window.log.toPlainText())
        self.assertTrue(self.window.folder_button.isEnabled())

    def test_failed_start_is_visible(self):
        self.window.url.setText("https://example.com")
        with patch.dict(os.environ, {"PATH": "/nonexistent"}):
            self.window.start_download()
            self.wait_for(lambda: not self.window.active)
        self.assertIn("실행하지 못했습니다", self.window.status.text())
        self.assertIn("실행 오류", self.window.log.toPlainText())


if __name__ == "__main__":
    unittest.main()
