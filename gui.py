#!/usr/bin/env python3
"""Qt launcher that streams worker output without opening a terminal."""

import codecs
import os
from pathlib import Path
import signal
import sys
from urllib.parse import urlsplit

from PySide6.QtCore import QProcess, QTimer
from PySide6.QtGui import QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)


class DownloadWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube 다운로드")
        self.resize(900, 580)
        self.url = QLineEdit()
        self.url.setPlaceholderText("영상 · 재생목록 · 채널 URL을 입력하세요")
        self.start_button = QPushButton("다운로드")
        self.stop_button = QPushButton("중단")
        self.stop_button.setEnabled(False)
        self.status = QLabel("주소를 입력한 후 다운로드를 누르세요.")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.log.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        controls = QHBoxLayout()
        controls.addWidget(self.url, 1)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.status)
        layout.addWidget(self.log, 1)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        params = QProcess.UnixProcessParameters()
        params.flags = QProcess.UnixProcessFlag.CreateNewSession
        self.process.setUnixProcessParameters(params)
        self.process.started.connect(self.worker_started)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.worker_finished)
        self.process.errorOccurred.connect(self.worker_error)
        self.kill_timer = QTimer(self)
        self.kill_timer.setSingleShot(True)
        self.kill_timer.setInterval(2000)
        self.kill_timer.timeout.connect(self.kill_remaining)
        self.group_id = None
        self.active = False
        self.cancelled = False
        self.close_pending = False
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.start_button.clicked.connect(self.start_download)
        self.url.returnPressed.connect(self.start_download)
        self.stop_button.clicked.connect(self.stop_download)

    def append_log(self, text):
        scrollbar = self.log.verticalScrollBar()
        follow = scrollbar.value() >= scrollbar.maximum() - 4
        cursor = QTextCursor(self.log.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if follow:
            scrollbar.setValue(scrollbar.maximum())

    def start_download(self):
        if self.active:
            return
        url = self.url.text().strip()
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme in ("https", "http") and bool(parsed.hostname)
        except ValueError:
            valid = False
        if not valid:
            self.status.setText("http:// 또는 https://로 시작하는 URL을 입력해 주세요.")
            self.url.setFocus()
            return
        self.log.clear()
        self.decoder.reset()
        self.cancelled = False
        self.active = True
        self.group_id = None
        self.url.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status.setText("다운로드 준비 중…")
        self.process.setProgram("bash")
        self.process.setArguments([str(Path(__file__).resolve().with_name("yt-dlp.sh")), url])
        self.process.start()

    def worker_started(self):
        self.group_id = self.process.processId()
        self.process.closeWriteChannel()
        if self.cancelled:
            self.terminate_group()
        else:
            self.status.setText("다운로드 중 — 진행 상황과 오류가 아래에 표시됩니다.")

    def read_output(self):
        data = bytes(self.process.readAllStandardOutput())
        self.append_log(self.decoder.decode(data).replace("\r", ""))

    def worker_finished(self, code, exit_status):
        self.read_output()
        self.append_log(self.decoder.decode(b"", final=True))
        if self.cancelled:
            # Wait for the grace timer to also stop any surviving descendants.
            if not self.kill_timer.isActive():
                self.finish("다운로드를 중단했습니다.")
        elif code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self.finish("다운로드 완료 — 저장 위치와 로그를 확인하세요.")
        else:
            self.finish(f"다운로드 실패 (종료 코드 {code}) — 아래 오류를 확인하세요.")

    def worker_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.append_log(f"실행 오류: {self.process.errorString()}\n")
            self.finish("다운로드 프로그램을 실행하지 못했습니다.")

    def send_group_signal(self, sig):
        if self.group_id:
            try:
                os.killpg(self.group_id, sig)
            except ProcessLookupError:
                pass

    def terminate_group(self):
        self.send_group_signal(signal.SIGTERM)
        self.kill_timer.start()

    def stop_download(self):
        if not self.active or self.cancelled:
            return
        self.cancelled = True
        self.stop_button.setEnabled(False)
        self.status.setText("다운로드를 중단하는 중…")
        if self.group_id:
            self.terminate_group()

    def kill_remaining(self):
        self.send_group_signal(signal.SIGKILL)
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.finish("다운로드를 중단했습니다.")

    def finish(self, message):
        self.active = False
        self.group_id = None
        self.status.setText(message)
        self.url.setEnabled(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.close_pending:
            self.close()

    def closeEvent(self, event):
        if self.active:
            self.close_pending = True
            self.stop_download()
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadWindow()
    window.show()
    sys.exit(app.exec())
