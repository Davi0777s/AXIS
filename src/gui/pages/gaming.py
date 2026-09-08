"""Gaming Tuner page — FPS, resolution, GPU, CPU, and performance controls."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QSlider, QGridLayout, QScrollArea, QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot

from src.core.runner import ScriptRunner, ScriptResult
from src.device.manager import DeviceManager
from src.gui.widgets.log_viewer import LogViewer


class _AdHocWorker(QThread):
    output = Signal(str)
    finished = Signal(object)

    def __init__(self, runner: ScriptRunner, commands: list[str], serial: str | None = None) -> None:
        super().__init__()
        self._runner = runner
        self._commands = commands
        self._serial = serial

    def run(self) -> None:
        lines: list[str] = []
        all_ok = True
        for cmd in self._commands:
            self.output.emit(f"$ {cmd}")
            r = self._runner.run_adb("shell", cmd, serial=self._serial)
            if r.stdout:
                for line in r.stdout.splitlines():
                    self.output.emit(f"  {line}")
            if not r.success:
                all_ok = False
                self.output.emit(f"  [FAIL] {r.output}")
        self.finished.emit(ScriptResult(all_ok, "\n".join(lines), 0 if all_ok else 1))


class GamingPage(QWidget):
    def __init__(
        self,
        runner: ScriptRunner,
        device_manager: DeviceManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._dm = device_manager
        self._worker: _AdHocWorker | None = None

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

        title = QLabel("Gaming Tuner")
        title.setProperty("class", "title")
        layout.addWidget(title)

        subtitle = QLabel("Tune resolution, FPS, GPU, CPU and performance in real-time")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # ---- TAB: TUNING ----
        tuning = QWidget()
        tuning_layout = QVBoxLayout(tuning)
        tuning_layout.setContentsMargins(16, 16, 16, 16)
        tuning_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)

        res_group = self._make_resolution_card()
        grid.addWidget(res_group, 0, 0)

        fps_group = self._make_fps_card()
        grid.addWidget(fps_group, 0, 1)

        gpu_group = self._make_gpu_card()
        grid.addWidget(gpu_group, 1, 0)

        cpu_group = self._make_cpu_card()
        grid.addWidget(cpu_group, 1, 1)

        tuning_layout.addLayout(grid)

        action_row = QHBoxLayout()
        self._apply_btn = QPushButton("\u21bb  Apply Settings")
        self._apply_btn.setProperty("class", "action-btn")
        self._apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_btn.clicked.connect(self._apply_settings)
        action_row.addWidget(self._apply_btn)

        self._reset_btn = QPushButton("\u21ba  Reset Defaults")
        self._reset_btn.setProperty("class", "secondary-btn")
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset_defaults)
        action_row.addWidget(self._reset_btn)
        action_row.addStretch()
        tuning_layout.addLayout(action_row)
        tuning_layout.addStretch()

        self._tabs.addTab(tuning, "TUNING")

        # ---- TAB: LAUNCHERS ----
        launch = QWidget()
        launch_layout = QVBoxLayout(launch)
        launch_layout.setContentsMargins(16, 16, 16, 16)
        launch_layout.setSpacing(12)

        launch_cards = QHBoxLayout()
        self._launch_game_btn = QPushButton("\u25b6  Launch Game Mode with Settings")
        self._launch_game_btn.setProperty("class", "action-btn")
        self._launch_game_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_game_btn.setToolTip(
            "Lanza scrcpy_game.sh usando la resolución y FPS elegidos arriba "
            "(aplica tuning GPU/CPU y arranca Shizuku/GG Mouse)."
        )
        self._launch_game_btn.clicked.connect(self._launch_game_with_settings)
        launch_cards.addWidget(self._launch_game_btn)

        self._launch_daily_btn = QPushButton("\u25af  Launch Daily Use")
        self._launch_daily_btn.setProperty("class", "secondary-btn")
        self._launch_daily_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_daily_btn.clicked.connect(self._launch_daily_use)
        launch_cards.addWidget(self._launch_daily_btn)
        launch_cards.addStretch()
        launch_layout.addLayout(launch_cards)

        launch_sub = QLabel("Quick presets")
        launch_sub.setProperty("class", "section-title")
        launch_layout.addWidget(launch_sub)

        presets_row = QHBoxLayout()
        for label, script in [
            ("\u25b6 Full Game Mode", "scripts/game_mode.sh"),
            ("\u21c9 Fix WiFi SAE", "scripts/reinstall_wifi_sae_fix.sh"),
            ("\u25c9 See Screen", "scripts/see_screen.sh"),
        ]:
            btn = QPushButton(label)
            btn.setProperty("class", "action-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=script: self._run_preset(s))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        launch_layout.addLayout(presets_row)
        launch_layout.addStretch()

        self._tabs.addTab(launch, "LAUNCHERS")

        # ---- TAB: LOG ----
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(16, 16, 16, 16)

        log_label = QLabel("Output Log")
        log_label.setProperty("class", "section-title")
        log_layout.addWidget(log_label)

        self._log = LogViewer()
        self._log.setMinimumHeight(160)
        log_layout.addWidget(self._log)

        self._tabs.addTab(log_tab, "LOG")

        layout.addStretch()
        scroll.setWidget(content)

    def _make_resolution_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("\u25c7  Stream Resolution")
        lbl.setProperty("class", "hdr")
        layout.addWidget(lbl)

        desc = QLabel("Max stream size (scales video only, not device display)")
        desc.setProperty("class", "subtitle")
        layout.addWidget(desc)

        self._res_slider = QSlider(Qt.Orientation.Horizontal)
        self._res_slider.setRange(480, 1920)
        self._res_slider.setValue(800)
        self._res_slider.setTickInterval(64)
        self._res_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        layout.addWidget(self._res_slider)

        self._res_label = QLabel("800 px")
        self._res_label.setProperty("class", "status-info")
        layout.addWidget(self._res_label)

        self._res_slider.valueChanged.connect(
            lambda v: self._res_label.setText(f"{v} px")
        )

        presets = QGridLayout()
        presets.setSpacing(8)
        for idx, val in enumerate([480, 720, 800, 1024, 1080, 1920]):
            btn = QPushButton(f"{val} px")
            btn.setProperty("class", "secondary-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, v=val: self._res_slider.setValue(v))
            presets.addWidget(btn, idx // 3, idx % 3)
            presets.setColumnStretch(idx % 3, 1)
        layout.addLayout(presets)

        return card

    def _make_fps_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("\u25c8  Target FPS")
        lbl.setProperty("class", "hdr")
        layout.addWidget(lbl)

        desc = QLabel("60fps recommended (panel is 90Hz, game caps at ~60)")
        desc.setProperty("class", "subtitle")
        layout.addWidget(desc)

        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["30", "60", "90", "120"])
        self._fps_combo.setCurrentText("60")
        layout.addWidget(self._fps_combo)

        presets = QGridLayout()
        presets.setSpacing(8)
        for idx, val in enumerate([30, 60, 90, 120]):
            btn = QPushButton(f"{val} FPS")
            btn.setProperty("class", "secondary-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda checked, v=val: self._fps_combo.setCurrentText(str(v))
            )
            presets.addWidget(btn, idx // 2, idx % 2)
            presets.setColumnStretch(idx % 2, 1)
        layout.addLayout(presets)

        return card

    def _make_gpu_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("\u25a1  GPU Settings")
        lbl.setProperty("class", "hdr")
        layout.addWidget(lbl)

        self._gpu_no_nap = QCheckBox("Force no nap (no micro-stutter)")
        self._gpu_no_nap.setChecked(True)
        layout.addWidget(self._gpu_no_nap)

        self._gpu_force_on = QCheckBox("Force rail/clk/bus on")
        self._gpu_force_on.setChecked(True)
        layout.addWidget(self._gpu_force_on)

        gpu_min_row = QHBoxLayout()
        gpu_min_row.addWidget(QLabel("Min power level:"))
        self._gpu_min_spin = QSpinBox()
        self._gpu_min_spin.setRange(0, 10)
        self._gpu_min_spin.setValue(5)
        gpu_min_row.addWidget(self._gpu_min_spin)
        layout.addLayout(gpu_min_row)

        gpu_max_row = QHBoxLayout()
        gpu_max_row.addWidget(QLabel("Max power level:"))
        self._gpu_max_spin = QSpinBox()
        self._gpu_max_spin.setRange(0, 10)
        self._gpu_max_spin.setValue(0)
        gpu_max_row.addWidget(self._gpu_max_spin)
        layout.addLayout(gpu_max_row)

        return card

    def _make_cpu_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("\u2699  CPU Settings")
        lbl.setProperty("class", "hdr")
        layout.addWidget(lbl)

        self._cpu_governor = QCheckBox("Use schedutil (demand-based, cooler)")
        self._cpu_governor.setChecked(True)
        layout.addWidget(self._cpu_governor)

        self._cpu_unlock_thermal = QCheckBox("Unlock thermal ceiling")
        self._cpu_unlock_thermal.setChecked(True)
        layout.addWidget(self._cpu_unlock_thermal)

        self._disable_anims = QCheckBox("Disable UI animations")
        self._disable_anims.setChecked(True)
        layout.addWidget(self._disable_anims)

        self._fix_refresh = QCheckBox("Lock display to 60Hz")
        self._fix_refresh.setChecked(True)
        layout.addWidget(self._fix_refresh)

        return card

    def _collect_commands(self) -> list[str]:
        cmds: list[str] = []
        fps = self._fps_combo.currentText()
        res = self._res_slider.value()

        if self._cpu_governor.isChecked():
            cmds.append("for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo schedutil > $c 2>/dev/null; done")

        if self._cpu_unlock_thermal.isChecked():
            cmds.append(
                "for cd in /sys/class/thermal/cooling_device*; do "
                "t=$(cat $cd/type 2>/dev/null); "
                "case $t in thermal-cpufreq-*) "
                "id=${t#thermal-cpufreq-}; "
                "echo 0 > $cd/cur_state 2>/dev/null; "
                "maxf=$(cat /sys/devices/system/cpu/cpufreq/policy$id/scaling_available_frequencies 2>/dev/null | tr ' ' '\\n' | sort -n | tail -1); "
                "[ -n \"$maxf\" ] && echo $maxf > /sys/devices/system/cpu/cpufreq/policy$id/scaling_max_freq 2>/dev/null; "
                "esac; done; true"
            )

        if self._gpu_no_nap.isChecked() or self._gpu_force_on.isChecked():
            flags = []
            if self._gpu_no_nap.isChecked():
                flags.append("force_no_nap")
            if self._gpu_force_on.isChecked():
                flags.extend(["force_clk_on", "force_bus_on", "force_rail_on"])
            cmds.append(
                f"K=/sys/class/kgsl/kgsl-3d0; "
                f"echo {self._gpu_min_spin.value()} > $K/min_pwrlevel 2>/dev/null; "
                f"echo {self._gpu_max_spin.value()} > $K/max_pwrlevel 2>/dev/null; "
                + "; ".join(f"echo 1 > $K/{f} 2>/dev/null" for f in flags)
                + "; echo 0 > $K/bus_split 2>/dev/null; true"
            )

        if self._fix_refresh.isChecked():
            cmds.append(
                "settings put global min_refresh_rate 60 2>/dev/null; "
                "settings put global peak_refresh_rate 60 2>/dev/null; "
                "settings put system min_refresh_rate 60 2>/dev/null; "
                "settings put system peak_refresh_rate 60 2>/dev/null; true"
            )

        if self._disable_anims.isChecked():
            cmds.append(
                "settings put global window_animation_scale 0 2>/dev/null; "
                "settings put global transition_animation_scale 0 2>/dev/null; "
                "settings put global animator_duration_scale 0 2>/dev/null; true"
            )

        cmds.append("echo 30 > /proc/sys/vm/swappiness 2>/dev/null")

        return cmds

    def _apply_settings(self) -> None:
        if not self._dm.is_connected():
            self._log.append_log("[ERROR] No device connected")
            return
        if self._worker and self._worker.isRunning():
            self._log.append_log("[WARN] Already applying settings...")
            return

        cmds = self._collect_commands()
        serial = self._dm.current_device.serial if self._dm.current_device else None
        self._log.clear_log()
        self._log.append_log("[APPLY] Applying gaming settings...")
        self._apply_btn.setEnabled(False)

        self._worker = _AdHocWorker(self._runner, cmds, serial)
        self._worker.output.connect(self._log.append_log)
        self._worker.finished.connect(self._on_apply_done)
        self._worker.start()

    def _on_apply_done(self, result: object) -> None:
        self._apply_btn.setEnabled(True)
        if isinstance(result, ScriptResult):
            state = "OK" if result.success else "FAILED"
            self._log.append_log(f"[{state}] Settings applied (exit: {result.returncode})")

    def _reset_defaults(self) -> None:
        self._res_slider.setValue(800)
        self._fps_combo.setCurrentText("60")
        self._gpu_min_spin.setValue(5)
        self._gpu_max_spin.setValue(0)
        self._gpu_no_nap.setChecked(True)
        self._gpu_force_on.setChecked(True)
        self._cpu_governor.setChecked(True)
        self._cpu_unlock_thermal.setChecked(True)
        self._disable_anims.setChecked(True)
        self._fix_refresh.setChecked(True)
        self._log.clear_log()
        self._log.append_log("[RESET] Defaults restored")

    def _run_preset(self, script: str) -> None:
        if not self._dm.is_connected():
            self._log.append_log("[ERROR] No device connected")
            return
        self._log.clear_log()
        self._log.append_log(f"[RUN] {script}...")
        serial = self._dm.current_device.serial if self._dm.current_device else None
        self._worker = _AdHocWorker(self._runner, [], serial)
        env = {}
        if serial:
            env["SERIAL"] = serial
        def _run():
            r = self._runner.run_script(script, env, on_output=self._log.append_log)
            self._worker.finished.emit(r)
        from threading import Thread
        t = Thread(target=_run, daemon=True)
        t.start()

    def _launch_game_with_settings(self) -> None:
        """Launch scrcpy_game.sh with the resolution/FPS chosen in the tuner."""
        if not self._dm.is_connected():
            self._log.append_log("[ERROR] No device connected. Connect via USB.")
            return
        res = str(self._res_slider.value())
        fps = self._fps_combo.currentText()
        serial = self._dm.current_device.serial if self._dm.current_device else None

        env: dict[str, str] = {"RES": res, "FPS": fps}
        if serial:
            env["SERIAL"] = serial

        self._log.clear_log()
        self._log.append_log(f"[LAUNCH] scrcpy_game.sh RES={res} FPS={fps} ...")
        self._launch_game_btn.setEnabled(False)
        self._worker = _AdHocWorker(self._runner, [], serial)
        self._worker.output.connect(self._log.append_log)

        def _run() -> None:
            r = self._runner.run_script("scripts/scrcpy_game.sh", env, on_output=self._log.append_log)
            self._worker.finished.emit(r)

        t = Thread(target=_run, daemon=True)
        t.start()

    def _launch_daily_use(self) -> None:
        """Launch scrcpy_daily.sh for standard phone use."""
        if not self._dm.is_connected():
            self._log.append_log("[ERROR] No device connected. Connect via USB.")
            return
        serial = self._dm.current_device.serial if self._dm.current_device else None
        env = {}
        if serial:
            env["SERIAL"] = serial

        self._log.clear_log()
        self._log.append_log("[LAUNCH] scrcpy_daily.sh ...")
        self._worker = _AdHocWorker(self._runner, [], serial)
        self._worker.output.connect(self._log.append_log)

        def _run() -> None:
            r = self._runner.run_script("scripts/scrcpy_daily.sh", env, on_output=self._log.append_log)
            self._worker.finished.emit(r)

        t = Thread(target=_run, daemon=True)
        t.start()
