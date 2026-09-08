"""Doctor page — system diagnostics with pass/fail indicators."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QHBoxLayout,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QBrush

from src.device.manager import DeviceManager
from src.doctor.diagnostics import DiagnosticsEngine, CheckResult, Severity


class _DiagWorker(QThread):
    finished = Signal(list)

    def __init__(self, engine: DiagnosticsEngine, shell_fn: object) -> None:
        super().__init__()
        self._engine = engine
        self._shell = shell_fn

    def run(self) -> None:
        try:
            results = self._engine.run_all(self._shell)
        except Exception:
            results = [CheckResult("Connection", Severity.ERROR, "Could not communicate with device")]
        self.finished.emit(results)


class DoctorPage(QWidget):
    def __init__(self, device_manager: DeviceManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dm = device_manager
        self._engine = DiagnosticsEngine()
        self._worker: _DiagWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("System Doctor")
        title.setProperty("class", "title")
        layout.addWidget(title)

        subtitle = QLabel("Run diagnostics to check device health and configuration")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self._run_btn = QPushButton("\u271a  Run Diagnostics")
        self._run_btn.setProperty("class", "action-btn")
        self._run_btn.clicked.connect(self._run_diagnostics)
        btn_row.addWidget(self._run_btn)

        self._refresh_btn = QPushButton("\u21ba  Refresh Device")
        self._refresh_btn.setProperty("class", "secondary-btn")
        self._refresh_btn.clicked.connect(lambda: self._dm.refresh())
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Check", "Status", "Details"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(1, 120)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        layout.addStretch()

    def _run_diagnostics(self) -> None:
        if not self._dm.is_connected():
            self._set_results([CheckResult("Device", Severity.ERROR, "No device connected. Connect via USB and enable debugging.")])
            return
        self._run_btn.setEnabled(False)
        self._run_btn.setText("Running...")
        self._worker = _DiagWorker(self._engine, self._dm.shell)
        self._worker.finished.connect(self._on_results)
        self._worker.start()

    def _on_results(self, results: list[object]) -> None:
        self._set_results([r for r in results if isinstance(r, CheckResult)])
        self._run_btn.setEnabled(True)
        self._run_btn.setText("\u271a  Run Diagnostics")

    def _set_results(self, results: list[CheckResult]) -> None:
        self._table.setRowCount(len(results))
        for i, r in enumerate(results):
            name_item = QTableWidgetItem(r.name)
            status_item = QTableWidgetItem(f"{r.icon}  {r.severity.value.upper()}")
            detail_item = QTableWidgetItem(r.message)

            severity_colors = {
                Severity.OK: "#4ade80",
                Severity.WARNING: "#fbbf24",
                Severity.ERROR: "#f87171",
                Severity.INFO: "#60a5fa",
            }
            color = severity_colors.get(r.severity, "#e0e0e0")
            name_item.setForeground(self._table.palette().color(self._table.foregroundRole()))
            status_item.setForeground(QBrush(QColor(color)))
            status_item.setText(f"{r.severity.value.upper()}")
            detail_item.setForeground(self._table.palette().color(self._table.foregroundRole()))

            self._table.setItem(i, 0, name_item)
            self._table.setItem(i, 1, status_item)
            self._table.setItem(i, 2, detail_item)
