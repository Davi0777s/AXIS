"""Main window — sidebar + topbar + stacked pages + status bar."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QStatusBar, QLabel,
)
from PySide6.QtCore import QTimer, Qt

from src.core.config import load as load_config
from src.core.runner import ScriptRunner
from src.device.manager import DeviceManager
from src.gui.assets import load_icon
from src.gui.widgets.sidebar import Sidebar
from src.gui.widgets.right_sidebar import RightSidebar
from src.gui.widgets.connection_banner import ConnectionBanner
from src.gui.pages.dashboard import DashboardPage
from src.gui.pages.launchers import LaunchersPage
from src.gui.pages.gaming import GamingPage
from src.gui.pages.boot_page import BootPage
from src.gui.pages.doctor_page import DoctorPage
from src.gui.pages.recovery_page import RecoveryPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AXIS — Android eXploration & Inspection Suite — by Davi0777s")
        icon = load_icon("axis.ico")
        if icon is not None:
            self.setWindowIcon(icon)
        self.setMinimumSize(1180, 760)
        self.setObjectName("central")

        self._config = load_config()
        self._device_manager = DeviceManager()
        self._runner = ScriptRunner(str(self._config.root))

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)

        self._right_sidebar = RightSidebar()

        # Right column: topbar + stacked pages
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self._build_topbar())

        self._connection_banner = ConnectionBanner()
        self._connection_banner.set_on_scan(self._poll_device)
        right_layout.addWidget(self._connection_banner)

        self._stack = QStackedWidget()
        self._launchers_page = LaunchersPage(self._runner)
        self._pages = [
            DashboardPage(self._device_manager, on_daily_use=self._start_daily_use),
            self._launchers_page,
            GamingPage(self._runner, self._device_manager),
            BootPage(),
            DoctorPage(self._device_manager),
            RecoveryPage(self._device_manager),
        ]
        for page in self._pages:
            self._stack.addWidget(page)
        right_layout.addWidget(self._stack, 1)

        root.addWidget(self._sidebar)
        root.addWidget(right, 1)
        root.addWidget(self._right_sidebar)

        self._setup_status_bar()
        self._start_device_polling()

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(52)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        self._crumb = QLabel("Dashboard")
        self._crumb.setObjectName("topbar-title")
        layout.addWidget(self._crumb)

        layout.addStretch()

        # Device tag (squared, technical)
        self._top_badge = QLabel("NO DEVICE")
        self._top_badge.setProperty("class", "tag tag-offline")
        self._top_badge.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._top_badge)

        return bar

    def _setup_status_bar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self._status_label = QLabel("No device connected")
        self._status_label.setObjectName("status-text")
        self._status_label.setTextFormat(Qt.TextFormat.PlainText)
        status.addPermanentWidget(self._status_label)
        # subtle left-aligned cached info
        self._status_side = QLabel("AXIS · by Davi0777s")
        self._status_side.setObjectName("status-text")
        status.addWidget(self._status_side)

    def _start_device_polling(self) -> None:
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_device)
        self._poll_timer.start(3000)
        self._poll_device()

    def _poll_device(self) -> None:
        device = self._device_manager.refresh()
        self._sidebar.set_device(device)
        self._connection_banner.refresh(device)

        if device is not None and device.state == "device":
            self._status_label.setText(
                f"{device.model or device.serial} ({device.state}) — Android {device.android_version}"
            )
            self._status_label.setProperty("class", "status-ok")
            model = (device.model or device.serial or "DEVICE").upper()
            self._top_badge.setText(f"{model}")
            self._top_badge.setProperty("class", "tag tag-online")
            self._right_sidebar.set_session(
                "Connected",
                info=(device.model or device.serial).upper(),
                detail=f"{device.state.upper()} · ANDROID {device.android_version}",
            )
        elif device is not None and device.state in ("unauthorized", "offline"):
            self._status_label.setText(
                f"{device.serial} — ADB {device.state.upper()}"
            )
            self._status_label.setProperty("class", "status-error")
            self._top_badge.setText(device.state.upper())
            self._top_badge.setProperty("class", "tag tag-offline")
            self._right_sidebar.set_session(
                "ADB blocked",
                info=device.state.upper(),
                detail="REAUTHORIZE TO CONNECT",
            )
        elif device is not None and device.state == "bootloader":
            self._status_label.setText("Fastboot — bootloader mode")
            self._status_label.setProperty("class", "status-warn")
            self._top_badge.setText("FASTBOOT")
            self._top_badge.setProperty("class", "tag tag-boot")
            self._right_sidebar.set_session(
                "Fastboot",
                info="BOOTLOADER",
                detail="ADB UNAVAILABLE",
            )
        else:
            self._status_label.setText("No device connected")
            self._status_label.setProperty("class", "status-warn")
            self._top_badge.setText("NO DEVICE")
            self._top_badge.setProperty("class", "tag tag-offline")
            self._right_sidebar.set_session(
                "Not connected",
                info="Awaiting device",
                detail="CONNECT VIA USB / ADB",
            )
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self._top_badge.style().unpolish(self._top_badge)
        self._top_badge.style().polish(self._top_badge)

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._crumb.setText(self._sidebar.page_title(index))

    def _start_daily_use(self) -> None:
        """Jump to Launchers and kick off Daily Use (dashboard CTA)."""
        self._switch_page(1)
        self._launchers_page.launch("scripts/scrcpy_daily.sh")
