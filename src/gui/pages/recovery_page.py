"""Recovery page — trigger recovery tools from the GUI."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame,
    QHBoxLayout, QScrollArea, QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal

from src.device.manager import DeviceManager
from src.recovery.wifi_fix import WiFiFix
from src.recovery.pin_remove import PINRemove
from src.recovery.screen_unlock import ScreenUnlock
from src.recovery.game_mode import GameMode
from src.gui.widgets.log_viewer import LogViewer

# Destructive tools wipe device credentials or change security behavior and
# must be confirmed before running.
_DESTRUCTIVE: dict[str, str] = {
    "PIN Remove": "Borra la credencial de bloqueo (PIN/patrón) del dispositivo. "
                  "La pantalla de bloqueo quedará desprotegida.",
    "Screen Unlock": "Desactiva el bloqueo de pantalla y deja el dispositivo "
                     "despierto indefinidamente mientras carga.",
}


class _RecoveryWorker(QThread):
    finished = Signal(str, bool, str)

    def __init__(self, tool_name: str, tool_obj: object, shell_fn: object) -> None:
        super().__init__()
        self._name = tool_name
        self._tool = tool_obj
        self._shell = shell_fn

    def run(self) -> None:
        try:
            result = self._tool.run(self._shell)
            self.finished.emit(self._name, result.success, result.message)
        except Exception as exc:
            self.finished.emit(self._name, False, str(exc))


class _ToolCard(QFrame):
    def __init__(
        self,
        name: str,
        description: str,
        on_click: object,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "tool")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(88)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(name)
        title.setProperty("class", "tool-name")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        desc = QLabel(description)
        desc.setProperty("class", "tool-desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._btn = QPushButton("\u25b6  Run")
        self._btn.setProperty("class", "action-btn")
        self._btn.setFixedWidth(100)
        self._btn.clicked.connect(on_click)
        layout.addWidget(self._btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self._state = QLabel("READY")
        self._state.setProperty("class", "run-state")
        self._state.setProperty("state", "idle")
        layout.addWidget(self._state)

    def set_status(self, text: str, state: str) -> None:
        self._state.setText(text)
        self._state.setProperty("state", state)
        self._state.style().unpolish(self._state)
        self._state.style().polish(self._state)


class RecoveryPage(QWidget):
    def __init__(self, device_manager: DeviceManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dm = device_manager
        self._tools = {
            "WiFi SAE Fix": WiFiFix(),
            "PIN Remove": PINRemove(),
            "Screen Unlock": ScreenUnlock(),
            "Game Mode": GameMode(),
        }
        self._worker: _RecoveryWorker | None = None
        self._cards: dict[str, _ToolCard] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Recovery Tools")
        title.setProperty("class", "title")
        layout.addWidget(title)

        subtitle = QLabel("One-click fixes for common Android issues")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # ---- TAB: TOOLS ----
        tools_tab = QWidget()
        tools_layout = QVBoxLayout(tools_tab)
        tools_layout.setContentsMargins(16, 16, 16, 16)
        tools_layout.setSpacing(12)

        grid = QHBoxLayout()
        grid.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(12)
        for name, tool in self._tools.items():
            card = _ToolCard(name, tool.DESCRIPTION, lambda n=name: self._run_tool(n))
            col.addWidget(card)
            self._cards[name] = card
        grid.addLayout(col)
        grid.addStretch()
        tools_layout.addLayout(grid)
        tools_layout.addStretch()

        self._tabs.addTab(tools_tab, "TOOLS")

        # ---- TAB: LOG ----
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(16, 16, 16, 16)

        log_title = QLabel("Output Log")
        log_title.setProperty("class", "section-title")
        log_layout.addWidget(log_title)

        self._log = LogViewer()
        self._log.setMinimumHeight(180)
        log_layout.addWidget(self._log)

        self._tabs.addTab(log_tab, "LOG")

        layout.addStretch()
        scroll.setWidget(content)

    def _run_tool(self, name: str) -> None:
        if not self._dm.is_connected():
            self._log.append_log(f"[ERROR] No device connected for {name}")
            return
        tool = self._tools.get(name)
        if not tool:
            return
        warning = _DESTRUCTIVE.get(name)
        if warning:
            from PySide6.QtWidgets import QMessageBox
            confirm = QMessageBox.question(
                self,
                "Confirmar acción destructiva",
                f"{warning}\n\n¿Continuar con «{name}» en el dispositivo conectado?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                self._log.append_log(f"[CANCEL] {name} no ejecutada (confirmación requerida)")
                return
        self._log.append_log(f"[RUNNING] {name}...")
        card = self._cards.get(name)
        if card:
            card.set_status("RUNNING", "running")
            card._btn.setEnabled(False)
        self._worker = _RecoveryWorker(name, tool, self._dm.shell)
        self._worker.finished.connect(self._on_result)
        self._worker.start()

    def _on_result(self, name: str, success: bool, message: str) -> None:
        icon = "OK" if success else "FAIL"
        self._log.append_log(f"[{icon}] {name}: {message}")
        card = self._cards.get(name)
        if card:
            card.set_status("DONE" if success else "FAILED", "ok" if success else "failed")
            card._btn.setEnabled(True)
