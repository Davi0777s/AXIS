"""Launchers page — one-click launch for daily use and gaming modes."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QComboBox, QSpinBox, QCheckBox, QGroupBox, QGridLayout,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot

from src.core.runner import ScriptRunner, ScriptResult
from src.gui.widgets.log_viewer import LogViewer


class _ScriptWorker(QThread):
    output = Signal(str)
    finished = Signal(object)

    def __init__(
        self,
        runner: ScriptRunner,
        script: str,
        env: dict[str, str] | None = None,
        timeout: float = 120.0,
    ) -> None:
        super().__init__()
        self._runner = runner
        self._script = script
        self._env = env
        self._timeout = timeout

    def run(self) -> None:
        result = self._runner.run_script(self._script, self._env, on_output=self.output.emit, timeout=self._timeout)
        self.finished.emit(result)

    def stop(self) -> None:
        self._runner.stop()


class _LauncherCard(QFrame):
    launched = Signal(str, dict)

    def __init__(
        self,
        title: str,
        description: str,
        script: str,
        icon: str = "\u25b6",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumHeight(140)
        self._script = script
        self._title_text = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title_label = QLabel(f"{icon}  {title}")
        title_label.setProperty("class", "hdr")
        header.addWidget(title_label)
        header.addStretch()

        self._status = QLabel("READY")
        self._status.setProperty("class", "run-state")
        self._status.setProperty("state", "idle")
        header.addWidget(self._status)
        layout.addLayout(header)

        desc = QLabel(description)
        desc.setProperty("class", "subtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._launch_btn = QPushButton(f"Launch {title}")
        self._launch_btn.setProperty("class", "action-btn")
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.clicked.connect(self._on_launch)
        layout.addWidget(self._launch_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    @property
    def script(self) -> str:
        return self._script

    def _on_launch(self) -> None:
        self.launched.emit(self._script, {})

    def set_status(self, text: str, state: str) -> None:
        self._status.setText(text)
        self._status.setProperty("state", state)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def set_busy(self, busy: bool) -> None:
        self._launch_btn.setEnabled(not busy)
        self._launch_btn.setText("Launching..." if busy else f"Launch {self._title_text}")


class LaunchersPage(QWidget):
    def __init__(self, runner: ScriptRunner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._runner = runner
        self._worker: _ScriptWorker | None = None
        self._active_card: _LauncherCard | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Launchers")
        title.setProperty("class", "title")
        layout.addWidget(title)

        subtitle = QLabel("One-click launch for phone modes — daily use, gaming, screen mirror")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        self._cards: list[_LauncherCard] = []
        card_grid = QGridLayout()
        card_grid.setSpacing(12)

        def add_card(card: _LauncherCard) -> None:
            card.launched.connect(self._launch_script)
            self._cards.append(card)
            pos = len(self._cards) - 1
            card_grid.addWidget(card, pos // 2, pos % 2)

        self._daily_card = _LauncherCard(
            "Daily Use",
            "Vertical screen, normal mouse/keyboard, audio enabled. "
            "For browsing, calls, videos — standard phone usage from your PC.",
            "scripts/scrcpy_daily.sh",
            "\u25af",
        )
        add_card(self._daily_card)

        self._gaming_card = _LauncherCard(
            "Gaming Mode",
            "Landscape, UHID mouse+keyboard for GG Mouse, performance mode, "
            "Shizuku, 60fps. Optimized for Free Fire and competitive games.",
            "scripts/scrcpy_game.sh",
            "\u25ad",
        )
        add_card(self._gaming_card)

        self._screen_card = _LauncherCard(
            "See Screen",
            "Capture a single screenshot and open scrcpy for live viewing. "
            "Quick way to see the device display.",
            "scripts/see_screen.sh",
            "\u25c9",
        )
        add_card(self._screen_card)

        self._shizuku_card = _LauncherCard(
            "Start Shizuku",
            "Start Shizuku server as root and activate GG Mouse. "
            "Required before gaming with mouse mapping.",
            "scripts/start_shizuku.sh",
            "\u21c9",
        )
        add_card(self._shizuku_card)

        layout.addLayout(card_grid)

        stop_row = QHBoxLayout()
        self._stop_btn = QPushButton("\u25a0  Stop Current")
        self._stop_btn.setProperty("class", "secondary-btn")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        stop_row.addWidget(self._stop_btn)
        stop_row.addStretch()
        layout.addLayout(stop_row)

        log_label = QLabel("Output Log")
        log_label.setProperty("class", "section-title")
        layout.addWidget(log_label)

        self._log = LogViewer()
        self._log.setMinimumHeight(180)
        layout.addWidget(self._log)

        layout.addStretch()
        scroll.setWidget(content)

    def _card_for_script(self, script: str) -> _LauncherCard | None:
        for card in self._cards:
            if card.script == script:
                return card
        return None

    def launch(self, script: str, env: dict[str, str] | None = None) -> None:
        """Public entry point (e.g. dashboard "Daily Use" CTA)."""
        self._launch_script(script, env or {})

    @Slot(str, dict)
    def _launch_script(self, script: str, env: dict[str, str]) -> None:
        if self._worker and self._worker.isRunning():
            self._log.append_log("[WARN] A script is already running. Stop it first.")
            return

        card = self._card_for_script(script)
        self._active_card = card

        self._log.clear_log()
        self._log.append_log(f"[LAUNCH] {script}...")
        self._stop_btn.setEnabled(True)
        if card:
            card.set_status("STARTING", "starting")
            card.set_busy(True)

        self._worker = _ScriptWorker(
            self._runner,
            script,
            env or None,
            timeout=self._timeout_for(script),
        )
        self._worker.output.connect(self._on_output)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _timeout_for(self, script: str) -> float:
        # scrcpy apps stay open indefinitely; unlimited timeout.
        # Ad-hoc helpers (see_screen, start_shizuku) should never hang forever.
        if "scrcpy_" in script:
            return 0.0
        return 120.0

    def _on_output(self, line: str) -> None:
        self._log.append_log(line)
        if self._active_card:
            self._active_card.set_status("RUNNING", "running")

    def _on_finished(self, result: object) -> None:
        self._stop_btn.setEnabled(False)
        card = self._active_card
        if card:
            card.set_busy(False)
        if isinstance(result, ScriptResult):
            if result.success:
                text = "DONE"
                state = "ok"
            elif result.returncode == -2 or "timed out" in result.output:
                text = "STOPPED"
                state = "stopped"
            else:
                text = "FAILED"
                state = "failed"
            if card:
                card.set_status(text, state)
            self._log.append_log(f"[DONE] exit code: {result.returncode}")
            if not result.success:
                self._log.append_log(result.output)
        self._active_card = None

    def _stop(self) -> None:
        if self._worker:
            self._worker.stop()
            self._log.append_log("[STOP] Sending stop signal...")
