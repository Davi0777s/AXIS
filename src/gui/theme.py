"""AXIS design system — metal & gothic engineering console.

Personality: a heavy-machine instrument panel. Deep graphite-carbone surfaces with
a subtle vertical steel sheen, cold platinum type, burnt gold/bronze signal accents,
glass-sharp 1px bevels, and corners cut down to a technical 2/3/4px (no pills).

Rules kept from frontend-ui-engineering:
  - no purple/indigo base, no loud gradients, no pill everything, no emoji chrome
  - gradient is used as a restrained vertical "metal sheen", never decorative washes
  - 4px spacing grid; consistent radius tier 2/3/4px
  - contrast on all text pairs; status never color-alone (text + glyph)
"""

DARK_THEME = """
/* ------------------------------------------------------------
   Tokens (raw QSS values; intent documented above)
   bg-carbone  #0a0a0d / #0f0f14 / #17171d / #1e1e26
   edge        #23232e / #33333f / #2b2b38 (top bevel light)
   platinum    #e8eaf0 / #b8bcc8 / #9aa0ad / #5c6270
   gold        #c9a24b / #d9b45f / #a37f2e
   verdigris   #5aa876   crimson #c75b57   steel #7a93b8
   ------------------------------------------------------------ */

* {
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #e8eaf0;
    outline: none;
}

QMainWindow, QWidget#central {
    background-color: #0f0f14;
    color: #e8eaf0;
}

QToolTip {
    background-color: #17171d;
    color: #e8eaf0;
    border: 1px solid #33333f;
    padding: 6px 10px;
    border-radius: 3px;
}

/* ============================================================
   Top bar — forged plate
   ============================================================ */
QWidget#topbar {
    background-color: #0c0c10;
    border-bottom: 1px solid #23232e;
}
QLabel#topbar-title {
    font-family: 'Georgia', 'Palatino Linotype', serif;
    font-size: 15px;
    font-weight: 700;
    color: #eaeaf2;
}
QLabel#topbar-crumb { font-size: 11px; color: #5c6270; }
QLabel#topbar-crumb-sep { font-size: 11px; color: #33333f; }
QLabel#topbar-device {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    color: #9aa0ad;
}
QFrame#topbar-sep {
    background-color: #23232e;
    max-width: 1px;
    min-width: 1px;
}

/* ============================================================
   Connection banner — reactive strip when no/blocked device
   ============================================================ */
QWidget#connection-banner {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2e2716, stop:1 #1c1810);
    border-bottom: 1px solid #6e5a24;
}
QLabel#connection-banner-icon {
    font-size: 17px;
    color: #dcbe7a;
    font-weight: 700;
}
QLabel#connection-banner-text {
    font-size: 12px;
    color: #cfd3dd;
}

/* Squared tag */
QLabel.tag {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 3px 8px;
    border-radius: 3px;
    border: 1px solid;
}
QLabel.tag-online {
    color: #7ed0a2;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1c2a23, stop:1 #151b18);
    border-color: #2f5a44;
}
QLabel.tag-offline {
    color: #e08d88;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e1d1c, stop:1 #1a1313);
    border-color: #6e3330;
}
QLabel.tag-boot {
    color: #dcbe7a;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e2716, stop:1 #1c1810);
    border-color: #6e5a24;
}
QLabel.tag-recovery {
    color: #9db8d8;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1c2430, stop:1 #141820);
    border-color: #3a4f6e;
}
QLabel.tag-muted {
    color: #8a8f9c;
    background-color: #17171d;
    border-color: #23232e;
}

/* ============================================================
   Sidebar — carbone panel
   ============================================================ */
QWidget#sidebar, QWidget#sidebar-right {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a0a0d, stop:0.5 #0d0d11, stop:1 #0a0a0d);
    border-right: 1px solid #23232e;
}
QWidget#sidebar-right { border-right: none; border-left: 1px solid #23232e; }
QLabel#sidebar-brand {
    font-family: 'Georgia', 'Palatino Linotype', serif;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: 5px;
    color: #e5e6ee;
}
QFrame#sidebar-brand-line {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6e5a24, stop:0.5 #c9a24b, stop:1 #6e5a24);
    min-height: 2px;
    max-height: 2px;
}
QLabel#sidebar-brand-sub {
    font-size: 9px;
    color: #8a8f9c;
    letter-spacing: 1.6px;
}
QLabel#sidebar-section {
    font-size: 10px;
    font-weight: 700;
    color: #8a8f9c;
    letter-spacing: 1.5px;
    padding: 0 4px 4px 12px;
}

QFrame#sidebar-device {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17171d, stop:1 #101014);
    border: 1px solid #23232e;
    border-radius: 3px;
    padding: 0;
}
QLabel#sidebar-device-top { font-size: 12px; font-weight: 700; }
QLabel#sidebar-device-sub {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 10px;
    color: #8a8f9c;
}

QPushButton.nav-btn {
    background: transparent;
    color: #a6acb8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 8px 12px;
    text-align: left;
    font-size: 12.5px;
    font-weight: 400;
}
QPushButton.nav-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1c1c24, stop:1 #14141b);
    color: #e8eaf0;
}
QPushButton.nav-btn:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #26220f, stop:1 #1b180a);
    color: #dcbe7a;
    border-left: 3px solid #c9a24b;
    font-weight: 600;
}
QLabel#sidebar-footer {
    font-size: 9px;
    color: #6a7080;
    padding: 8px 4px;
}
QFrame#sidebar-sep {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0a0a0d, stop:0.5 #33333f, stop:1 #0a0a0d);
    min-height: 1px;
    max-height: 1px;
}

/* ============================================================
   ADB panel (dashboard) — connection health + main authorize
   ============================================================ */
QWidget#adb-panel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #17171d, stop:1 #101014);
    border: 1px solid #23232e;
    border-top: 1px solid #2b2b38;
    border-radius: 4px;
}
QWidget#adb-panel[class="alert"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2e1d1c, stop:1 #1a1313);
    border: 1px solid #6e3330;
    border-top: 1px solid #8a3d39;
}
QWidget#adb-panel-status { font-size: 12px; font-weight: 600; }

QPushButton.big-btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #d9b45f, stop:1 #a37f2e);
    color: #14110a;
    border: 1px solid #8a6a24;
    border-top: 1px solid #e2c47c;
    border-radius: 3px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.4px;
}
QPushButton.big-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e6c574, stop:1 #b48933);
    border-color: #9a752a;
}
QPushButton.big-btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #9a752a, stop:1 #a37f2e);
}
QPushButton.big-btn:disabled {
    background: #17171d;
    color: #5c6270;
    border: 1px solid #23232e;
}

/* ============================================================
   Typography
   ============================================================ */
QLabel.title {
    font-family: 'Georgia', 'Palatino Linotype', serif;
    font-size: 21px;
    font-weight: 700;
    color: #f0f1f7;
}
QLabel.subtitle { font-size: 12.5px; color: #9aa0ad; }
QLabel.section-title {
    font-size: 11px;
    font-weight: 700;
    color: #c9a24b;
    letter-spacing: 1.4px;
}
QLabel.hdr { font-size: 13px; font-weight: 600; color: #cfd3dd; }
QLabel.mono, QLabel.mono-pad {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    color: #a6acb8;
}
QLabel.mono-pad {
    padding: 2px 6px;
    background-color: #0f0f14;
    border: 1px solid #23232e;
    border-radius: 3px;
}

QLabel.status-ok    { color: #7ed0a2; font-weight: 600; }
QLabel.status-warn  { color: #dcbe7a; font-weight: 600; }
QLabel.status-error { color: #e08d88; font-weight: 600; }
QLabel.status-info  { color: #9db8d8; font-weight: 600; }

QLabel.run-state { font-size: 10px; font-weight: 700; letter-spacing: 0.9px; }
QLabel.run-state[state="idle"]     { color: #6a7080; }
QLabel.run-state[state="starting"] { color: #dcbe7a; }
QLabel.run-state[state="running"]  { color: #9db8d8; }
QLabel.run-state[state="ok"]       { color: #7ed0a2; }
QLabel.run-state[state="stopped"]  { color: #8a8f9c; }
QLabel.run-state[state="failed"]   { color: #e08d88; }

QLabel.verdict-ok    { font-size: 14px; font-weight: 600; color: #7ed0a2; }
QLabel.verdict-bad   { font-size: 14px; font-weight: 600; color: #e08d88; }
QLabel.verdict-issue { font-size: 12.5px; color: #dcbe7a; }

/* ============================================================
   Surfaces — iron plates
   ============================================================ */
QFrame.card {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a22, stop:1 #131319);
    border: 1px solid #23232e;
    border-top: 1px solid #2b2b38;
    border-radius: 4px;
}
QFrame.card:hover {
    border: 1px solid #33333f;
    border-top: 1px solid #3a3a49;
}

QFrame.tool {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a22, stop:1 #131319);
    border: 1px solid #23232e;
    border-top: 1px solid #2b2b38;
    border-radius: 4px;
}
QFrame.tool:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #20202a, stop:1 #17171d);
    border: 1px solid #33333f;
    border-top: 1px solid #3a3a49;
}
QLabel.tool-icon {
    font-size: 18px;
    color: #c9a24b;
    font-weight: 600;
}
QLabel.tool-name { font-size: 13px; font-weight: 600; color: #cfd3dd; }
QLabel.tool-desc { font-size: 11.5px; color: #9aa0ad; }

QLabel.spec-key {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.9px;
    color: #6a7080;
}
QLabel.spec-val {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    color: #a6acb8;
}

/* ============================================================
   Buttons — chased brass & steel
   ============================================================ */
QPushButton { border-radius: 2px; }

QPushButton.action-btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #d9b45f, stop:1 #a37f2e);
    color: #14110a;
    border: 1px solid #8a6a24;
    border-top: 1px solid #e2c47c;
    border-radius: 2px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 700;
}
QPushButton.action-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e6c574, stop:1 #b48933);
    border-color: #9a752a;
}
QPushButton.action-btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #9a752a, stop:1 #a37f2e);
}
QPushButton.action-btn:disabled {
    background: #17171d;
    color: #5c6270;
    border: 1px solid #23232e;
}

QPushButton.secondary-btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #262630, stop:1 #181820);
    color: #b8bcc8;
    border: 1px solid #33333f;
    border-top: 1px solid #3d3d4a;
    border-radius: 2px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 500;
}
QPushButton.secondary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2c2c38, stop:1 #1c1c25);
    border-color: #43434f;
    color: #e8eaf0;
}
QPushButton.secondary-btn:pressed {
    background: #141414;
    border-color: #33333f;
}
QPushButton.secondary-btn:disabled { color: #5c6270; border-color: #23232e; }

QPushButton.danger-btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4a2321, stop:1 #2e1514);
    color: #e08d88;
    border: 1px solid #6e3330;
    border-radius: 2px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 600;
}
QPushButton.danger-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5a2b28, stop:1 #3a1c1a);
    color: #eca49f;
}

QPushButton.icon-btn {
    background-color: #17171d;
    color: #9aa0ad;
    border: 1px solid #23232e;
    border-radius: 2px;
    padding: 3px 8px;
    font-size: 12px;
}
QPushButton.icon-btn:hover { background-color: #1e1e26; color: #e8eaf0; border-color: #33333f; }

QPushButton:focus { border: 1px solid #c9a24b; }
QPushButton:disabled { cursor: forbidden; }

/* ============================================================
   Tabs — engraved steel bar
   ============================================================ */
QTabWidget::pane {
    border: 1px solid #23232e;
    border-top: none;
    border-radius: 0 0 4px 4px;
    background: #111116;
    top: -1px;
}
QTabBar {
    background: #0c0c10;
}
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #20202a, stop:1 #16161d);
    color: #9aa0ad;
    border: 1px solid #23232e;
    border-bottom: none;
    border-top: 2px solid #2b2b38;
    border-radius: 3px 3px 0 0;
    padding: 6px 18px;
    margin-right: 2px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
QTabBar::tab:hover { color: #e8eaf0; }
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2e2812, stop:1 #1c1810);
    color: #dcbe7a;
    border-top: 2px solid #c9a24b;
    border-bottom: none;
    font-weight: 700;
}
QTabBar::tab:first { margin-left: 6px; }

/* ============================================================
   Inputs
   ============================================================ */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #0f0f14;
    color: #e8eaf0;
    border: 1px solid #33333f;
    border-radius: 2px;
    padding: 4px 8px;
    font-size: 12.5px;
    min-height: 20px;
    selection-background-color: #3a4a54;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #c9a24b;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9aa0ad;
    margin-right: 5px;
}
QComboBox QAbstractItemView {
    background-color: #17171d;
    color: #e8eaf0;
    border: 1px solid #33333f;
    border-radius: 2px;
    selection-background-color: #a37f2e;
    selection-color: #14110a;
    outline: none;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #1e1e26;
    border: none;
    border-radius: 1px;
    width: 14px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #33333f; }

QCheckBox { color: #c8ccd6; spacing: 8px; font-size: 12.5px; padding: 2px 0; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #43434f;
    border-radius: 2px;
    background-color: #0f0f14;
}
QCheckBox::indicator:hover { border-color: #c9a24b; }
QCheckBox::indicator:checked {
    background-color: #a37f2e;
    border-color: #c9a24b;
}

QSlider::groove:horizontal { height: 4px; background-color: #23232e; border-radius: 1px; }
QSlider::sub-page:horizontal {
    background-color: #a37f2e;
    border-radius: 1px;
}
QSlider::handle:horizontal {
    width: 13px; height: 13px;
    margin: -5px 0;
    border-radius: 2px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d9d9e2, stop:1 #8a8f9c);
    border: 1px solid #33333f;
}
QSlider::handle:horizontal:hover { background-color: #ffffff; }

/* ============================================================
   Log / code
   ============================================================ */
QPlainTextEdit, QTextEdit {
    background-color: #0a0a0c;
    color: #aab8a4;
    border: 1px solid #23232e;
    border-radius: 2px;
    padding: 8px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    selection-background-color: rgba(201, 162, 75, 0.30);
}
QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid #c9a24b; }

/* ============================================================
   Tables
   ============================================================ */
QTableWidget, QTableView {
    background-color: #0f0f14;
    alternate-background-color: #131318;
    border: 1px solid #23232e;
    border-radius: 2px;
    gridline-color: #23232e;
    color: #c8ccd6;
}
QTableWidget::item, QTableView::item { padding: 5px 8px; border: none; }
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(201, 162, 75, 0.25);
    color: #f0f1f7;
}
QTableCornerButton::section { background-color: #0c0c10; border: none; }
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17171d, stop:1 #0f0f14);
    color: #9aa0ad;
    border: none;
    border-bottom: 1px solid #33333f;
    border-right: 1px solid #23232e;
    padding: 6px 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QHeaderView::section:hover { color: #e8eaf0; }

/* ============================================================
   Scrollbars
   ============================================================ */
QScrollBar:vertical { background: transparent; width: 9px; margin: 0; }
QScrollBar::handle:vertical {
    background: #33333f;
    border-radius: 2px;
    min-height: 28px;
    margin: 2px;
    border: 1px solid #23232e;
}
QScrollBar::handle:vertical:hover { background: #43434f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 9px; }
QScrollBar::handle:horizontal {
    background: #33333f;
    border-radius: 2px;
    min-width: 28px;
    margin: 2px;
    border: 1px solid #23232e;
}
QScrollBar::handle:horizontal:hover { background: #43434f; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ============================================================
   Status bar
   ============================================================ */
QStatusBar {
    background-color: #0c0c10;
    color: #9aa0ad;
    border-top: 1px solid #23232e;
    font-size: 12px;
}
QStatusBar::item { border: none; }
QLabel#status-text { font-size: 12px; padding: 2px 8px; }

/* ============================================================
   Misc
   ============================================================ */
QProgressBar {
    background-color: #0f0f14;
    border: 1px solid #23232e;
    border-radius: 2px;
    text-align: center;
    color: #c8ccd6;
    height: 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d9b45f, stop:1 #a37f2e);
    border-radius: 2px;
}

QGroupBox {
    background-color: #17171d;
    border: 1px solid #23232e;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: 600;
    color: #c8ccd6;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: #c9a24b;
    font-size: 12px;
    letter-spacing: 0.4px;
}

QMenu {
    background-color: #17171d;
    color: #e8eaf0;
    border: 1px solid #33333f;
    border-radius: 3px;
    padding: 4px;
}
QMenu::item { padding: 5px 20px; border-radius: 2px; }
QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d9b45f, stop:1 #a37f2e);
    color: #14110a;
}
QMenu::separator { height: 1px; background: #23232e; margin: 4px 6px; }

QMessageBox { background-color: #0f0f14; }

QSplitter::handle { background-color: #23232e; }
"""