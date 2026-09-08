"""Boot page — analyze boot images from file."""
from __future__ import annotations
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QFrame, QPlainTextEdit, QHBoxLayout,
)
from PySide6.QtCore import Qt, QThread, Signal

from src.analyzer.boot_analysis import BootAnalyzer, AnalysisReport


class _AnalyzeWorker(QThread):
    finished = Signal(object)

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def run(self) -> None:
        analyzer = BootAnalyzer()
        result = analyzer.analyze(self._path)
        self.finished.emit(result)


class BootPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._analyzer = BootAnalyzer()
        self._worker: _AnalyzeWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Boot Image Analyzer")
        title.setProperty("class", "title")
        layout.addWidget(title)

        subtitle = QLabel("Select a boot.img or vendor_boot.img to analyze")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        top_row = QHBoxLayout()
        self._file_label = QLabel("No file selected")
        self._file_label.setProperty("class", "subtitle")
        top_row.addWidget(self._file_label, 1)

        self._browse_btn = QPushButton("\u25a1  Browse")
        self._browse_btn.setProperty("class", "action-btn")
        self._browse_btn.clicked.connect(self._browse)
        top_row.addWidget(self._browse_btn)

        self._analyze_btn = QPushButton("\u25b6  Analyze")
        self._analyze_btn.setProperty("class", "action-btn")
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.clicked.connect(self._analyze)
        top_row.addWidget(self._analyze_btn)

        layout.addLayout(top_row)

        self._result_card = QFrame()
        self._result_card.setProperty("class", "card")
        card_layout = QVBoxLayout(self._result_card)
        self._result_label = QLabel("Load a boot image to see analysis results")
        self._result_label.setProperty("class", "subtitle")
        self._result_label.setWordWrap(True)
        card_layout.addWidget(self._result_label)
        layout.addWidget(self._result_card)

        self._json_view = QPlainTextEdit()
        self._json_view.setReadOnly(True)
        self._json_view.setPlaceholderText("Detailed analysis will appear here...")
        self._json_view.setMinimumHeight(250)
        layout.addWidget(self._json_view)

        layout.addStretch()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Boot Image", "",
            "Boot images (*.img);;All files (*)"
        )
        if path:
            self._file_label.setText(path)
            self._analyze_btn.setEnabled(True)
            self._result_label.setText("Ready to analyze")
            self._json_view.clear()

    def _analyze(self) -> None:
        path = self._file_label.text()
        if not path or path == "No file selected":
            return
        self._analyze_btn.setEnabled(False)
        self._result_label.setText("Analyzing...")
        self._worker = _AnalyzeWorker(path)
        self._worker.finished.connect(self._on_result)
        self._worker.start()

    def _on_result(self, report: object) -> None:
        if not isinstance(report, AnalysisReport):
            return
        color = "#4ade80" if report.is_valid else "#f87171"
        self._result_label.setText(
            f"<span style='color:{color}; font-size:15px; font-weight:600'>{report.summary}</span>"
        )
        if report.issues:
            self._result_label.setText(
                self._result_label.text()
                + f"<br><span style='color:#fbbf24'>Issues: {'; '.join(report.issues)}</span>"
            )
        self._json_view.setPlainText(json.dumps(report.to_dict(), indent=2))
        self._analyze_btn.setEnabled(True)
